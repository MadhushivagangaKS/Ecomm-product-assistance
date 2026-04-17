import csv
import time
import re
import os
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class FlipkartScraper:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_top_reviews(self,product_url,count=2):
        """Get the top reviews for a product.
        """
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = uc.Chrome(options=options,use_subprocess=True)

        if not product_url.startswith("http"):
            driver.quit()
            return "No reviews found"

        try:
            driver.get(product_url)
            time.sleep(4)
            
            # Try multiple close button strategies
            close_attempts = [
                ("XPath close button", By.XPATH, "//button[contains(text(), '✕')]"),
                ("XPath close button alt", By.XPATH, "//button[contains(@aria-label, 'close')]"),
                ("CSS close button", By.CSS_SELECTOR, "button[aria-label*='close' i]"),
            ]
            
            for name, by, selector in close_attempts:
                try:
                    driver.find_element(by, selector).click()
                    time.sleep(1)
                    break
                except Exception:
                    continue

            # Scroll down to load reviews
            for _ in range(4):
                ActionChains(driver).send_keys(Keys.END).perform()
                time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Try multiple selectors for review blocks (old and new structures)
            review_selectors = [
                "div._27M-vq",  # Old selector
                "div.col.EPCmJX",  # Alternative old
                "div._6K-7Co",  # Another alternative
                "div[class*='review']",  # Generic review div
            ]
            
            review_blocks = []
            for selector in review_selectors:
                try:
                    review_blocks = soup.select(selector)
                    if review_blocks:
                        break
                except Exception:
                    continue
            
            seen = set()
            reviews = []

            for block in review_blocks:
                text = block.get_text(separator=" ", strip=True)
                if text and text not in seen:
                    reviews.append(text)
                    seen.add(text)
                if len(reviews) >= count:
                    break
                    
        except Exception as e:
            print(f"Error occurred while scraping reviews: {e}")
            reviews = []
        finally:
            driver.quit()
            
        return " || ".join(reviews) if reviews else "No reviews found"
    
    def scrape_flipkart_products(self, query, max_products=1, review_count=2):
        """Scrape Flipkart products based on a search query.
        """
        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options,use_subprocess=True)
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(4)

        # Try to close popup - use multiple selector strategies
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
        except Exception:
            try:
                driver.find_element(By.XPATH, "//button[contains(@aria-label, 'close')]").click()
            except Exception:
                pass  # Popup may not exist, continue

        time.sleep(2)
        products = []

        items = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")[:max_products]
        for item in items:
            try:
                # Extract title
                title = item.find_element(By.CSS_SELECTOR, "div.RG5Slk").text.strip()
                
                # Extract price
                price = item.find_element(By.CSS_SELECTOR, "div.oFEPlD").text.strip()
                
                # Extract rating
                rating = item.find_element(By.CSS_SELECTOR, "div.MKiFS6").text.strip()
                
                # Extract reviews count - use multiple selector fallbacks
                total_reviews = "N/A"
                try:
                    # First try: span.PvbNMB (new structure from 2025/2026)
                    reviews_container = item.find_element(By.CSS_SELECTOR, "span.PvbNMB")
                    reviews_text = reviews_container.text.strip()
                    match = re.search(r"(\d+(?:,\d+)*)\s+Reviews", reviews_text)
                    if match:
                        total_reviews = match.group(1)
                except Exception:
                    try:
                        # Fallback: try div.vQDoqR (old structure)
                        reviews_container = item.find_element(By.CSS_SELECTOR, "div.vQDoqR")
                        reviews_text = reviews_container.text.strip()
                        match = re.search(r"(\d+(?:,\d+)*)\s+Reviews", reviews_text)
                        if match:
                            total_reviews = match.group(1)
                    except Exception:
                        # Last resort: search for any text containing "Reviews"
                        try:
                            all_text = item.text
                            match = re.search(r"(\d+(?:,\d+)*)\s+Reviews", all_text)
                            if match:
                                total_reviews = match.group(1)
                        except Exception:
                            pass
                
                # Extract product ID and link
                link_el = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
                href = link_el.get_attribute("href")
                product_link = href if href.startswith("http") else "https://www.flipkart.com" + href
                match = re.findall(r"/p/(itm[0-9A-Za-z]+)", href)
                product_id = match[0] if match else "N/A"
                
            except Exception as e:
                print(f"Error occurred while processing item: {e}")
                continue

            top_reviews = self.get_top_reviews(product_link, count=review_count) if "flipkart.com" in product_link else "Invalid product URL"
            products.append([product_id, title, rating, total_reviews, price, top_reviews])

        driver.quit()
        return products
    
    def save_to_csv(self, data, filename="product_reviews.csv"):
        """Save the scraped product reviews to a CSV file."""
        if os.path.isabs(filename):
            path = filename
        elif os.path.dirname(filename):  # filename includes subfolder like 'data/product_reviews.csv'
            path = filename
            os.makedirs(os.path.dirname(path), exist_ok=True)
        else:
            # plain filename like 'output.csv'
            path = os.path.join(self.output_dir, filename)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "product_title", "rating", "total_reviews", "price", "top_reviews"])
            writer.writerows(data)
        
"""
Utility script to inspect Flipkart page structure and find correct selectors
"""
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import json

def inspect_flipkart_page(product_url):
    """Inspect a Flipkart product page to find correct selectors."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        driver.get(product_url)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        print("\n" + "="*80)
        print("FLIPKART PAGE INSPECTION REPORT")
        print("="*80)
        
        # 1. Look for close buttons
        print("\n[1] CLOSE BUTTON CANDIDATES:")
        print("-" * 80)
        close_buttons = soup.find_all(["button", "div"], class_=lambda x: x and "close" in x.lower())
        if close_buttons:
            for i, btn in enumerate(close_buttons[:5], 1):
                print(f"  {i}. {btn.name} | class='{btn.get('class')}' | text='{btn.get_text(strip=True)[:50]}'")
        
        # Also search for specific symbols
        all_buttons = soup.find_all("button")
        symbol_buttons = [b for b in all_buttons if "✕" in b.get_text() or "✗" in b.get_text() or "×" in b.get_text()]
        if symbol_buttons:
            print("\n  Symbol buttons found:")
            for i, btn in enumerate(symbol_buttons[:3], 1):
                print(f"    {i}. {btn.get_text(strip=True)} | class='{btn.get('class')}'")
        
        # 2. Look for review-related elements
        print("\n[2] REVIEW COUNT CANDIDATES:")
        print("-" * 80)
        
        # Search by common review patterns
        all_divs = soup.find_all("div")
        review_divs = [d for d in all_divs if "review" in d.get_text().lower() and any(c.isdigit() for c in d.get_text())]
        
        if review_divs:
            for i, div in enumerate(review_divs[:5], 1):
                classes = div.get('class', [])
                text = div.get_text(strip=True)[:60]
                print(f"  {i}. class='{' '.join(classes)}' | text='{text}'")
        
        # 3. Product item structure
        print("\n[3] PRODUCT ITEM STRUCTURE:")
        print("-" * 80)
        
        # Look for product containers - common patterns
        product_containers = soup.find_all("div", {"data-id": True})
        if product_containers:
            print(f"  Found {len(product_containers)} items with data-id attribute")
            if product_containers:
                first_item = product_containers[0]
                print(f"\n  First item structure:")
                print(f"    {first_item.prettify()[:800]}...")
                
                # Check what's inside
                print(f"\n  Classes found in first item:")
                all_classes = set()
                for elem in first_item.find_all():
                    if elem.get('class'):
                        all_classes.update(elem.get('class'))
                
                for cls in sorted(list(all_classes))[:20]:
                    print(f"    - {cls}")
        
        # 4. Alternative selectors to try
        print("\n[4] RECOMMENDED SELECTORS TO TRY:")
        print("-" * 80)
        
        print("\n  For Close Button:")
        print("    - button[aria-label*='close' i]")
        print("    - button[title*='close' i]")
        print("    - [data-testid*='close']")
        print("    - .Modal__Header button")
        
        print("\n  For Review Count (inspect page and look for):")
        print("    - Text containing 'Reviews'")
        print("    - Look for rating/review divs in product list items")
        print("    - Try: span, div with numbers followed by 'Reviews'")
        
        # 5. Save full page source for manual inspection
        with open("flipkart_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n[5] Full page source saved to: flipkart_page_source.html")
        print("    Open this file in your browser to inspect the structure.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Example: Inspect a Flipkart product page
    product_url = input("Enter Flipkart product URL: ").strip()
    
    if not product_url.startswith("http"):
        print("Error: URL must start with http/https")
    else:
        inspect_flipkart_page(product_url)

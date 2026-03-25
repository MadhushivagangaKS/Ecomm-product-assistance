import importlib.metadata
packages = [
    "langchain",
    "langchain-mcp-adapters",
    "langchain_core",
    "python-dotenv",
    "langchain-openai"
    ]
for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} (not installed)")
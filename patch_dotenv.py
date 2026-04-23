import os

for filename in ["run_pipeline.py", "run_llm.py"]:
    with open(filename, "r") as f:
        content = f.read()

    if "from dotenv import load_dotenv" not in content:
        content = content.replace("import sys\n", "import sys\n\ntry:\n    from dotenv import load_dotenv\n    load_dotenv()\nexcept ImportError:\n    pass\n\n")

        with open(filename, "w") as f:
            f.write(content)
        print(f"Patched {filename}")

with open("README.md", "r") as f:
    readme = f.read()

if "python-dotenv" not in readme:
    readme = readme.replace("pip install pandas geopandas shapely anthropic matplotlib", "pip install pandas geopandas shapely anthropic matplotlib python-dotenv")
    with open("README.md", "w") as f:
        f.write(readme)
    print("Patched README.md")

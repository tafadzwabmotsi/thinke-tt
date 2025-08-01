- **Develop Core Modules:**

  - Create `scraper_tools.py` (or similar) with classes/functions for `PapacambridgeScraper`, `SavemyexamsScraper`, etc. Focus on **robustness** (error handling, retries, user-agent headers).
  - Create `download_tools.py` with `download_and_save_pdfs` and helper functions. Focus on **file path creation**, **chunked downloads**, and **handling existing files**.
  - **Crucially:** Ensure these functions have clear **type hints** and comprehensive **docstrings**, as these will directly inform the LLM about how to use them.

- **Thorough Testing:**

  - Write Python scripts to call your scraping and downloading functions directly with **hardcoded inputs**.
  - **Verify** that they successfully scrape links and download files to the correct locations.
  - Test **edge cases**: missing elements on a page, network errors, invalid URLs, large files.

- **ADK Integration:**
  - Once your core tools are solid, **create your ADK project**.
  - **Import** your `scraper_tools` and `download_tools` modules.
  - Define **`FunctionTool` wrappers** for each of your functions, making them available to your `LlmAgent`.
  - **Craft the initial prompt** for your `LlmAgent` to guide its behavior and specify its role (e.g., "You are a helpful past paper download assistant. You can search, scrape, and download academic papers...").
  - Start **testing the agent's ability** to understand natural language, choose the right tool, extract parameters, and handle follow-up questions.

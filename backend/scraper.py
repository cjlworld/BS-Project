import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def get_html(url, cookies):
    # Launch a new browser instance
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        # Add cookies to the context
        await context.add_cookies(cookies)
        
        page = await browser.new_page()
        
        # Navigate to the URL·
        await page.goto(url)
        await page.wait_for_load_state()
        
        # Get the HTML content of the page
        html_content = await page.content()
        
        # Close the browser
        await browser.close()
        
        return html_content

def parse_html(html_content):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

async def main():
    url = 'https://taobao.com'
    
    # Example cookies
    cookies = [
        {
            'name': '_tb_token_',
            'value': '359ead16abee',
            'domain': 'taobao.com',
            'path': '/',
        },
    ]
    
    html_content = await get_html(url, cookies)

    soup = parse_html(html_content)
    
    # Now you can work with the parsed HTML
    with open('soup.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))

# Run the main function
asyncio.run(main())
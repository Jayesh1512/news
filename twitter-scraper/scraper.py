"""
Twitter Scraper using Playwright
Scrapes tweets from specific accounts and stores in PostgreSQL via backend API
"""
import os
import asyncio
import httpx
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
TWITTER_ACCOUNTS = os.getenv("TWITTER_ACCOUNTS", "elonmusk,OpenAI,verge").split(",")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "900"))  # 15 minutes


async def scrape_twitter_account(page, username: str) -> list:
    """
    Scrape tweets from a Twitter account
    Returns list of tweet data dictionaries
    """
    tweets = []
    
    try:
        # Navigate to user's timeline
        url = f"https://twitter.com/{username}"
        logger.info(f"Scraping {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # Wait for dynamic content
        
        # Scroll to load tweets
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(1000)
        
        # Extract tweet articles
        tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
        logger.info(f"Found {len(tweet_elements)} tweets for @{username}")
        
        for element in tweet_elements[:10]:  # Limit to 10 most recent
            try:
                # Extract tweet text
                text_element = await element.query_selector('[data-testid="tweetText"]')
                text = await text_element.inner_text() if text_element else ""
                
                # Extract timestamp
                time_element = await element.query_selector('time')
                timestamp = await time_element.get_attribute('datetime') if time_element else None
                
                # Extract tweet link
                link_element = await element.query_selector('a[href*="/status/"]')
                link = await link_element.get_attribute('href') if link_element else None
                if link and not link.startswith('http'):
                    link = f"https://twitter.com{link}"
                
                if text and link:
                    tweets.append({
                        "title": f"@{username}: {text[:100]}{'...' if len(text) > 100 else ''}",
                        "content": text,
                        "url": link,
                        "source": "twitter",
                        "category": "technology",
                        "author": username,
                        "published_at": timestamp
                    })
            except Exception as e:
                logger.warning(f"Failed to extract tweet: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Failed to scrape @{username}: {e}")
    
    return tweets


async def save_tweets_to_backend(tweets: list):
    """Send scraped tweets to backend API"""
    if not tweets:
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for tweet in tweets:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/api/news/",
                    json=tweet
                )
                if response.status_code == 200:
                    logger.info(f"Saved tweet: {tweet['title'][:50]}")
                else:
                    logger.warning(f"Failed to save tweet: {response.status_code}")
            except Exception as e:
                logger.error(f"Error saving tweet: {e}")


async def scrape_all_accounts():
    """Scrape all configured Twitter accounts"""
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        # Note: Running without stealth mode - may be detected by Twitter
        # Add authentication or use official Twitter API for production
        
        all_tweets = []
        
        for username in TWITTER_ACCOUNTS:
            username = username.strip()
            if username:
                tweets = await scrape_twitter_account(page, username)
                all_tweets.extend(tweets)
                await asyncio.sleep(5)  # Rate limiting
        
        await browser.close()
        
        # Save to backend
        logger.info(f"Total tweets scraped: {len(all_tweets)}")
        await save_tweets_to_backend(all_tweets)


async def main():
    """Main loop - scrape periodically"""
    logger.info(f"Twitter scraper started. Accounts: {TWITTER_ACCOUNTS}")
    logger.info(f"Scrape interval: {SCRAPE_INTERVAL}s")
    
    while True:
        try:
            await scrape_all_accounts()
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
        
        logger.info(f"Waiting {SCRAPE_INTERVAL}s until next scrape...")
        await asyncio.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())

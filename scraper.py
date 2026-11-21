import asyncio
import json
import os
import random
import sys
from datetime import datetime
from twikit import Client
from twikit.errors import TooManyRequests

BASE_DIR = "/Users/frosty/x-scraper"
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "scraped_tweets.json")

TOPICS = [
    '("AI agents" OR "local LLM") -is:retweet lang:en',
]

MAX_NEW_TWEETS_PER_TOPIC = 60
MAX_REQUESTS_PER_RUN = 15


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def load_existing_tweets():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


async def scrape_all_topics():
    if "--now" not in sys.argv:
        startup_jitter = random.uniform(30, 240)
        log(f"Scheduled run triggered. Waiting {startup_jitter:.0f}s jitter before starting...")
        await asyncio.sleep(startup_jitter)

    client = Client("en-US")
    client.load_cookies(COOKIES_FILE)

    existing_tweets = load_existing_tweets()
    seen_ids = {str(t["id"]) for t in existing_tweets}
    all_new_tweets = []
    requests_made = 0

    for idx, query in enumerate(TOPICS):
        if requests_made >= MAX_REQUESTS_PER_RUN:
            log("Reached safe request cap for this run. Stopping early.")
            break

        log(f"Searching topic: {query}")
        topic_new_tweets = []

        try:
            tweets = await client.search_tweet(query, product="Latest")
            requests_made += 1

            while tweets and len(topic_new_tweets) < MAX_NEW_TWEETS_PER_TOPIC:
                hit_seen_tweet = False

                for tweet in tweets:
                    tweet_id = str(tweet.id)
                    if tweet_id in seen_ids:
                        hit_seen_tweet = True
                        break

                    topic_new_tweets.append({
                        "id": tweet_id,
                        "topic": query,
                        "user": tweet.user.screen_name,
                        "created_at": tweet.created_at,
                        "text": tweet.text,
                        "likes": tweet.favorite_count,
                        "retweets": tweet.retweet_count,
                    })
                    seen_ids.add(tweet_id)

                    if len(topic_new_tweets) >= MAX_NEW_TWEETS_PER_TOPIC:
                        break

                if hit_seen_tweet or requests_made >= MAX_REQUESTS_PER_RUN:
                    break

                await asyncio.sleep(random.uniform(5.0, 12.0))
                tweets = await tweets.next()
                requests_made += 1

            all_new_tweets.extend(topic_new_tweets)
            log(f"Collected {len(topic_new_tweets)} new tweets for this topic.")

            if idx < len(TOPICS) - 1 and requests_made < MAX_REQUESTS_PER_RUN:
                await asyncio.sleep(random.uniform(20.0, 45.0))

        except TooManyRequests:
            log("HTTP 429 rate limit hit. Aborting immediately until next scheduled run.")
            break
        except Exception as e:
            log(f"Error during scrape: {e}")
            break

    if all_new_tweets:
        updated_tweets = all_new_tweets + existing_tweets
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_tweets, f, indent=2, ensure_ascii=False)
        log(f"Saved {len(all_new_tweets)} new tweets (Total stored: {len(updated_tweets)}, Requests used: {requests_made}).")
    else:
        log(f"No new tweets found (Total stored: {len(existing_tweets)}, Requests used: {requests_made}).")


if __name__ == "__main__":
    asyncio.run(scrape_all_topics())

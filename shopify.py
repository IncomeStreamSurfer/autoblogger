import openai
import pandas as pd
import requests
import os
import base64
import time
from tqdm import tqdm
import concurrent.futures
import threading
import backoff
import json
from concurrent.futures import ThreadPoolExecutor

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)  # for exponential backoff

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10))
def completion_with_backoff(**kwargs):
    try:
        return openai.ChatCompletion.create(**kwargs)
    except openai.error.InvalidRequestError as e:
        print(f"Invalid request error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

openai.api_key = 'YOUR_OPEN_AI_kEY'

output_df = pd.DataFrame(columns=['URL Slug', 'Meta Title', 'Description', 'Blog Content', 'Featured Image'])
output_lock = threading.Lock()

# Shopify API credentials
api_key = 'YOUR_API_KEY'
password = 'YOUR_SHOPIFY_PASSWORD'
store_address = 'https://YOUR_STORE_ID.myshopify.com/admin'
blog_id = 'YOUR_BLOG_ID'
author = 'YOUR_AUTHOR_NAME'

# Headers for the request
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def create_shopify_post(payload):
    response = requests.post(
    f'{store_address}/blogs/{blog_id}/articles.json',
    headers=headers,
    data=json.dumps(payload),
    auth=(api_key, password)
)
    if response.status_code == 201:
        print(f"Successfully created post with ID: {response.json()['article']['id']}")
    else:
        print(f"Error creating post: {response.content}")
        response.raise_for_status()  # This will raise an exception if the request failed

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10))
def generate_blog_post(row):
    try:
        url_slug = row['URL Slug']
        meta_title = row['Meta Title']
        description = row['Description of Page']
        conversation_outline = [
    {
        "role": "system",
        "content": "You are an essay-writing assistant who creates detailed outlines for essays. You always write at least 15 points for each outline.",
    },
    {
        "role": "user",
        "content": f"Create an outline for an essay about {meta_title} with at least 15 titles.",
    },
]

        print(f"Generating outline for URL Slug {url_slug}")
        response_outline = completion_with_backoff(
            model="gpt-4",
            messages=conversation_outline,
            max_tokens=1024,
            temperature=0.2
        )
        essay_outline = response_outline['choices'][0]['message']['content']
        conversation = [
            {
                "role": "system",
                "content": f'Internal links are VITAL for  SEO. Please always use 5 internal links. Never mention essay. Write an article using the {essay_outline}. Internal links are vital to SEO. Please always include a maximum 5 ahref internal links contextually in the article not just at the end. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Always include 5 internal links. Output in HTML. Write an article using {essay_outline} with 3 paragraphs per heading. Each heading of the essay should have at least one list or table (with a small black border, and border between the rows and columns) also. It will go onto wordpress so I dont need opening HTML tags. Create relative links using the following relative links contextually thoughout the article. Use a maximum of 5. /suit-basics/, /suit-fit/, /how-to-wear-a-suit/, /how-to-measure/, /30-suit-basics/, /button-rules/, /suit-styles/, /how-to-clean/, /dress-pants-fit/, /suit-cuts/, /differences-in-suit-cuts/, /classic-fit-suit/, /slim-fit-suit/, /modern-fit-suit/, /three-piece-suit/, /double-breasted-suit/, /suit-vs-tuxedo/, /how-to-wear-a-tuxedo/, /blue-tuxedo/, /tuxedo-shirt/, /best-affordable-tuxedos/, /formal-attire/, /wedding-attire/, /black-tie/, /semi-formal/, /cocktail-attire/, /business-professional/, /job-interview/, /smart-casual/, /business-casual/, /funeral-attire/, /suit-color/, /color-combinations/, /blazer-trousers/, /dress-shirt-fit/, /how-to-wear-a-dress-shirt/, /dress-shirt-sizes/, /shirt-colors/, /best-dress-shirts/, /shirt-and-tie/, /ties-guide/, /bow-ties/, /match-the-watch/, /dress-shoes-styles/, /pocket-square/, /belts-guide/, /how-to-wear-a-belt/, /cufflinks/, /tie-clip/, /suspenders/, /sunglasses/, /suit-fabrics/, /wool/, /cotton/, /cashmere/, /velvet/, /linen/, /seersucker/, /tweed/, /polyester/, /sharkskin/, /polyester/, /sharkskin/',
            },
            {
                "role": "user",
                "content": f"Never leave an article incomplete, always write the entire thing. Make sure all content is relevant to the article. Use a fun tone of voice. Always include at least 5 internal links. Each heading from the essay outline should have at least 3 paragraphs and a table or list After writing the article, under H2 and H3 headers create an FAQ section, followed by FAQPage schema opening and closing with <script> tags.",
            },
        ]
        print(f"Generating blog content for URL Slug {url_slug}")
        response = completion_with_backoff(
            model="gpt-4",
            messages=conversation,
            max_tokens=4500,
            temperature=0.2
        )
        blog_content = response['choices'][0]['message']['content']
        print(f"Generated blog content for URL Slug {url_slug}")
        result = {'URL Slug': url_slug, 'Meta Title': meta_title, 'Description': description, 'Blog Content': blog_content,}
        with output_lock:
            global output_df
            output_df = pd.concat([output_df, pd.DataFrame([result])], ignore_index=True)
            output_df.to_csv('output.csv', index=False)
            print(f"Saved blog post for URL Slug {url_slug} to output.csv")

        # Prepare the payload for the Shopify API
        payload = {
            "article": {
                "title": meta_title,
                "author": author,
                "tags": "Blog Post, OpenAI",
                "body_html": blog_content
            }
        }

        # Send the POST request to the Shopify API
        print(f"Creating Shopify post for URL Slug {url_slug}")
        create_shopify_post(payload)

    except Exception as e:
        print(f"Error generating blog post for URL Slug {url_slug}: {e}")
        return None

def main():
    df = pd.read_csv('input.csv')

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(generate_blog_post, row) for index, row in df.iterrows()]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            try:
                future.result()  # To raise exceptions if any occurred during the thread's execution
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

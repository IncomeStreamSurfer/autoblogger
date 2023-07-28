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
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
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





openai.api_key = 'XX'

output_df = pd.DataFrame(columns=['URL Slug', 'Meta Title', 'Description', 'Blog Content', 'Featured Image'])
output_lock = threading.Lock()

# Retry on rate limit error with exponential backoff
@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10))
def generate_featured_image(text):
    api_key = 'XX'
    api_host = 'https://api.stability.ai'
    engine_id = 'stable-diffusion-xl-1024-v1-0'
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": f'an object-only patterned background representing classic style'
                }
            ],
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 768,
            "width": 1344,
            "samples": 1,
            "steps": 30,
        },
    )
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))
    data = response.json()
    image_base64 = data["artifacts"][0]["base64"]
    if not os.path.exists('./out'):
        os.makedirs('./out')
    image_filename = f"./out/{text.replace(' ', '_').replace('/', '_')}.png"
    with open(image_filename, "wb") as f:
        f.write(base64.b64decode(image_base64))
    return image_filename

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10))
def generate_blog_post(row):
    try:
        
        url_slug = row['URL Slug']
        meta_title = row['Meta Title']
        description = row['Description of Page']
        

        conversation_outline = [
            {
                "role": "system",
                "content": 'You are an essay-writing assistant who creates detailed outlines for essays. You always write at least 15 points for each outline.',
            },
            {
                "role": "user",
                "content": f"Create an outline for an essay about {meta_title} with at least 15 titles.",
            },
        ]
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
                "content": f'Never mention essay. Write an article using the {essay_outline}. Internal links are vital to SEO. Please always include a maximum 5 ahref internal links contextually in the article not just at the end. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Always include 5 internal links. Output in HTML. Write an article using {essay_outline} with 3 paragraphs per heading. Each heading of the essay should have at least one list or table (with a small black border, and border between the rows and columns) also. It will go onto wordpress so I dont need opening HTML tags. Create relative links using the following relative links contextually thoughout the article. Use a maximum of 5. /suit-basics/, /suit-fit/, /how-to-wear-a-suit/, /how-to-measure/, /30-suit-basics/, /button-rules/, /suit-styles/, /how-to-clean/, /dress-pants-fit/, /suit-cuts/, /differences-in-suit-cuts/, /classic-fit-suit/, /slim-fit-suit/, /modern-fit-suit/, /three-piece-suit/, /double-breasted-suit/, /suit-vs-tuxedo/, /how-to-wear-a-tuxedo/, /blue-tuxedo/, /tuxedo-shirt/, /best-affordable-tuxedos/, /formal-attire/, /wedding-attire/, /black-tie/, /semi-formal/, /cocktail-attire/, /business-professional/, /job-interview/, /smart-casual/, /business-casual/, /funeral-attire/, /suit-color/, /color-combinations/, /blazer-trousers/, /dress-shirt-fit/, /how-to-wear-a-dress-shirt/, /dress-shirt-sizes/, /shirt-colors/, /best-dress-shirts/, /shirt-and-tie/, /ties-guide/, /bow-ties/, /match-the-watch/, /dress-shoes-styles/, /pocket-square/, /belts-guide/, /how-to-wear-a-belt/, /cufflinks/, /tie-clip/, /suspenders/, /sunglasses/, /suit-fabrics/, /wool/, /cotton/, /cashmere/, /velvet/, /linen/, /seersucker/, /tweed/, /polyester/, /sharkskin/, /polyester/, /sharkskin/',
            },
            {
                "role": "user",
                "content": f"Never leave an article incomplete, always write the entire thing. Make sure all content is relevant to the article. Use a fun tone of voice. Always include at least 5 internal links. Each heading from the essay outline should have at least 3 paragraphs and a table or list After writing the article, under H2 and H3 headers create an FAQ section, followed by FAQPage schema opening and closing with <script> tags.",
            },
        ]
        response = completion_with_backoff(
    model="gpt-4",
    messages=conversation,
    max_tokens=4500,
    temperature=0.2
        )
        
        
        blog_content = response['choices'][0]['message']['content']
        tqdm.write(f"Generated blog content for URL Slug {url_slug}")
        featured_image = generate_featured_image(meta_title)
        tqdm.write(f"Generated featured image for URL Slug {url_slug}")
        result = {'URL Slug': url_slug, 'Meta Title': meta_title, 'Description': description, 'Blog Content': blog_content, 'Featured Image': featured_image}
        

        with output_lock:
            global output_df
            output_df = pd.concat([output_df, pd.DataFrame([result])], ignore_index=True)
            output_df.to_csv('output.csv', index=False)
            tqdm.write(f"Saved blog post for URL Slug {url_slug} to output.csv")
            

                       # WordPress site URL
            wp_url = 'https://giucas.com/'

            # WordPress username and password
            username = 'incomestreamsurfer@gmail.com'
            password = 'NRNG kjTV nAg3 XWM7 61b8 NOpk'

              # Open the image file in binary mode
            with open(result['Featured Image'], 'rb') as img:
                # Prepare the headers for the REST API request
                headers = {
                    'Content-Disposition': f'attachment; filename={os.path.basename(result["Featured Image"])}',
                    'Content-Type': 'image/png',  # Adjust this if your images are not PNGs
                    'Authorization': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
                }

                # Send the POST request to the WordPress REST API
                response = requests.post(f'{wp_url}/wp-json/wp/v2/media', headers=headers, data=img)

            # If the request was successful, the image ID will be in the response
            if response.status_code == 201:
                image_id = response.json()['id']
            else:
                print(f"Error uploading image: {response.content}")

            # Create a blog post in WordPress
            post = {
                "title": result['Meta Title'],
                "content": result['Blog Content'],
                "status": "publish",
                "excerpt": result['Description'],
                "slug": result['URL Slug'],
                "meta": {},
                "featured_media": image_id
            }

            # Send the POST request to create the post
            response = requests.post(f'{wp_url}/wp-json/wp/v2/posts', headers={
                'Authorization': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
            }, json=post)

            if response.status_code != 201:
                print(f"Error creating post: {response.content}")
            else:
                print(f"Successfully created post with ID: {response.json()['id']}")

    except Exception as e:
        tqdm.write(f"Error generating blog post for URL Slug {url_slug}: {e}")
        return None

df = pd.read_csv('input.csv')  # Assuming input CSV file name is 'input.csv'
rows = df.to_dict('records')

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(tqdm(executor.map(generate_blog_post, rows), total=len(rows)))


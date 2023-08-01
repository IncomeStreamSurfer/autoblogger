import openai
import pandas as pd
import requests
import os
import base64
import time
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
model_name = os.getenv('MODEL_NAME')

def generate_featured_image(brand):
    api_key = os.getenv('STABILITY_AI_API_KEY')
    api_host = 'https://api.stability.ai'
    engine_id = 'stable-diffusion-xl-beta-v2-2-2'
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
                    "text": f'Threads, stitches, clothes, mannequin, fabrics and other tailoring objects repeated patterned wallpaper'
                }
            ],
            "cfg_scale": 12,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 512,
            "width": 768,
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

    image_filename = f"./out/{brand.replace(' ', '_').replace('/', '_')}.png"
    with open(image_filename, "wb") as f:
        f.write(base64.b64decode(image_base64))

    return image_filename




df = pd.read_csv('input.csv')  # Assuming input CSV file name is 'input.csv'

# Initialize the blog data list
blog_data = []

# Initialize a counter
counter = 0

# Convert the DataFrame to a list of dictionaries for tqdm
rows = df.to_dict('records')

# Create a new dataframe to store the results
output_df = pd.DataFrame(columns=['URL Slug', 'Meta Title', 'Description', 'Blog Content', 'Featured Image'])

# Loop over each row with tqdm tracking progress
for index, row in enumerate(tqdm(rows, desc='Generating blog posts')):
    url_slug = row['URL Slug']
    meta_title = row['Meta Title']
    description = row['Description of Page']
    brand = row['Brand'] # This should match your csv column name
   
    # Step 1: Generate a detailed essay outline
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

    response_outline = openai.ChatCompletion.create(
        model=model_name,
        messages=conversation_outline,
        max_tokens = int(os.getenv('MAX_OUTLINE_TOKENS')),
        temperature = float(os.getenv('TEMPERATURE'))
    )

    essay_outline = response_outline['choices'][0]['message']['content']

      # Step 2: Generate a blog post based on the essay outline
    conversation = [
    {
        "role": "system",
        "content": f'Never mention essay. Write an article using the {essay_outline}. Internal links are vital to SEO. Please always include a maximum 5 ahref internal links contextually in the article not just at the end. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Always include 5 internal links. Output in HTML. Write an article using {essay_outline} with 3 paragraphs per heading. Each heading of the essay should have at least one list or table (with a small black border, and border between the rows and columns) also. It will go onto wordpress so I dont need opening HTML tags. Create relative links using the following relative links contextually thoughout the article. Use a maximum of 5. /suit-basics/, /suit-fit/, /how-to-wear-a-suit/, /how-to-measure/, /30-suit-basics/, /button-rules/, /suit-styles/, /how-to-clean/, /dress-pants-fit/, /suit-cuts/, /differences-in-suit-cuts/, /classic-fit-suit/, /slim-fit-suit/, /modern-fit-suit/, /three-piece-suit/, /double-breasted-suit/, /suit-vs-tuxedo/, /how-to-wear-a-tuxedo/, /blue-tuxedo/, /tuxedo-shirt/, /best-affordable-tuxedos/, /formal-attire/, /wedding-attire/, /black-tie/, /semi-formal/, /cocktail-attire/, /business-professional/, /job-interview/, /smart-casual/, /business-casual/, /funeral-attire/, /suit-color/, /color-combinations/, /blazer-trousers/, /dress-shirt-fit/, /how-to-wear-a-dress-shirt/, /dress-shirt-sizes/, /shirt-colors/, /best-dress-shirts/, /shirt-and-tie/, /ties-guide/, /bow-ties/, /match-the-watch/, /dress-shoes-styles/, /pocket-square/, /belts-guide/, /how-to-wear-a-belt/, /cufflinks/, /tie-clip/, /suspenders/, /sunglasses/, /suit-fabrics/, /wool/, /cotton/, /cashmere/, /velvet/, /linen/, /seersucker/, /tweed/, /polyester/, /sharkskin/, /polyester/, /sharkskin/',},
    {
        "role": "user",
        "content": f"Never leave an article incomplete, always write the entire thing. Make sure all content is relevant to the article. Use a fun tone of voice. Always include at least 5 internal links. Each heading from the essay outline should have at least 3 paragraphs and a table or list After writing the article, under H2 and H3 headers create an FAQ section, followed by FAQPage schema opening and closing with <script> tags.",
    },
]

    response = openai.ChatCompletion.create(
        model=model_name,
        messages=conversation,
        max_tokens = int(os.getenv('MAX_TOKENS')),
        temperature = float(os.getenv('TEMPERATURE'))
    )


    blog_content = response['choices'][0]['message']['content']

    # Generate featured image
    featured_image = generate_featured_image(brand)

    # Save the information into a new row in the output dataframe
    output_df = output_df._append({'URL Slug': url_slug, 'Meta Title': meta_title, 'Description': description, 'Blog Content': blog_content, 'Featured Image': featured_image}, ignore_index=True)
    
    # After each blog post is written, it's immediately saved to 'output.csv'
    output_df.to_csv('output.csv', index=False)

    # After generating 2 blog posts, sleep for 5 minutes (300 seconds)
    if (index + 1) % 2 == 0:
        time.sleep(300)

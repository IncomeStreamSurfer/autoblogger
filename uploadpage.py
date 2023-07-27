import pandas as pd
import requests
import base64
import os

# Load the CSV file into a pandas dataframe
df = pd.read_csv('output.csv')

wp_url = 'YOUR_WEBSITE_URL'

# WordPress username and password
username = 'YOUR_WORDPRESS_USERNAME'
password = 'YOUR_WP_APP_PASSWORD'

# Parent page ID
parent_page_id = 10

# Iterate through each row in the CSV file
for index, row in df.iterrows():
    # Open the image file in binary mode
    with open(row['Featured Image'], 'rb') as img:
        # Prepare the headers for the REST API request
        headers = {
            'Content-Disposition': f'attachment; filename={os.path.basename(row["Featured Image"])}',
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
        continue

    # Create a page in WordPress
    page = {
        "title": row['Meta Title'],
        "content": row['Blog Content'],
        "status": "publish",
        "excerpt": row['Description'],
        "slug": row['URL Slug'],
        "meta": {
        },
        "featured_media": image_id,
        "parent": 2536  # Set the parent page
    }

    # Send the POST request to create the page
    response = requests.post(f'{wp_url}/wp-json/wp/v2/pages', headers={
        'Authorization': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
    }, json=page)

    if response.status_code != 201:
        print(f"Error creating page: {response.content}")
    else:
        print(f"Successfully created page with ID: {response.json()['id']}")

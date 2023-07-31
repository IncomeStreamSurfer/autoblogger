# autoblogger
This is an autoblogger that uses the ChatGPT API and Stable Diffusion API to create fully optimized blog posts and post them automatically to wordpress

## First step

- Get your stability API key (I am using [dreamstudio]([url](https://dreamstudio.com/api/)))
- Get your OpenAI API Key (GPT-4 is recommended, haven't tested with GPT3.5, 300-500 articles cost me about $50)
- Create a WordPress App Password, get your user log-in, and your site's URL
- A plan for your website, this way you can already internally link without worrying about doing it afterwards. If you keep a nice, uniform structure, you will be able to plan out all the content and post it all to your website without using any other internal link system.

[Example Website](https://giucas.com)

**There are 5 different python scripts as of 31-07-2023**

## 1. test.py

Currently the best script for creating 500+ blog posts in a few hours. You can use ChatGPT to generate topical authority tables and then input all of it into a CSV, edit the featured image logic as shown below if you want something more specific for your niche/website (I had to make general images becasue stable diffusion still can't do hands properly)

This is the one script that does everything in one shot, instead of two separate scripts, one for creating the content and one for posting it, this particular autoblogging script does all of the actions at once.

Please note, this is quite csotly, so if you don't want to spend a lot of money, don't give it too many keywords.

This is the only script that is currently using Stable Diffusion XD1.0, you can easily add this engine to the other scripts, but honestly i'd recommend trying to get test.py to work first. Do it with 3-5 keywords and see if you like the results, then delete those articles and write all of your content in one go.

## 2. Createblogpost.py

This script has the logic to create a blog post. You can input the keywords from input.csv, which takes the arguments of URL Slug,Meta Title,Description of Page.

To either change the featured image prompt, or to add your own internal links, simply edit these lines in the script:

### Featured image:

                    "text": f'Threads, stitches, clothes, mannequin, fabrics and other tailoring objects repeated patterned wallpaper'
                    
An important point here is that if you're in a niche that doesn't require something like hands on humans, or text, then you can simply add something like f'a patterned image of {meta_title}

### ChatGPT Prompt:

        "content": f'Never mention essay. Write an article using the {essay_outline}. Internal links are vital to SEO. Please always include a maximum 5 ahref internal links contextually in the article not just at the end. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Always include 5 internal links. Output in HTML. Write an article using {essay_outline} with 3 paragraphs per heading. Each heading of the essay should have at least one list or table (with a small black border, and border between the rows and columns) also. It will go onto wordpress so I dont need opening HTML tags. Create relative links using the following relative links contextually thoughout the article. Use a maximum of 5. /suit-basics/, /suit-fit/, /how-to-wear-a-suit/, /how-to-measure/, /30-suit-basics/, /button-rules/, /suit-styles/, /how-to-clean/, /dress-pants-fit/, /suit-cuts/, /differences-in-suit-cuts/, /classic-fit-suit/, /slim-fit-suit/, /modern-fit-suit/, /three-piece-suit/, /double-breasted-suit/, /suit-vs-tuxedo/, /how-to-wear-a-tuxedo/, /blue-tuxedo/, /tuxedo-shirt/, /best-affordable-tuxedos/, /formal-attire/, /wedding-attire/, /black-tie/, /semi-formal/, /cocktail-attire/, /business-professional/, /job-interview/, /smart-casual/, /business-casual/, /funeral-attire/, /suit-color/, /color-combinations/, /blazer-trousers/, /dress-shirt-fit/, /how-to-wear-a-dress-shirt/, /dress-shirt-sizes/, /shirt-colors/, /best-dress-shirts/, /shirt-and-tie/, /ties-guide/, /bow-ties/, /match-the-watch/, /dress-shoes-styles/, /pocket-square/, /belts-guide/, /how-to-wear-a-belt/, /cufflinks/, /tie-clip/, /suspenders/, /sunglasses/, /suit-fabrics/, /wool/, /cotton/, /cashmere/, /velvet/, /linen/, /seersucker/, /tweed/, /polyester/, /sharkskin/, /polyester/, /sharkskin/',},

## createpage.py

Works in the same way but creates content for a page instead, it has slightly different logic in the prompt, but basically was a way for me to personally write different content about a different topic. 

The upload logic is more important, it's just the prompt that is slightly different here. 

## uploadblogpost.py

This script is specific for using after "createblogpost.py" and is used to upload that content as a blog post.

## uploadpage.py 

This script is specific for using after "createpage.py" and is used to upload that content as a page, if you want to change the parent page then you should change this line:

parent_page_id = 10









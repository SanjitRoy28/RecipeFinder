# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from bs4 import BeautifulSoup
import requests
from serpapi import GoogleSearch

app = Flask(__name__)
app.secret_key = 'recipe_scraper_secret_key'  # Needed for flash messages

# Getting a URL
def get_url():
    URL = 'https://pinchofyum.com/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 200:
        return response
    else:
        return None

# Scraping homepage for recipe categories
def scraping_homepage(response):
    soup = BeautifulSoup(response.content, 'lxml')
    choices = []
    ideas = soup.find_all('span')
    for idea in ideas:
        value = idea.text
        if "Recipes" in value:
            choices.append(value)
    return choices

# Convert category name to URL path
def process_category(category):
    if category == "Most Popular Recipes":
        return "popular"
    else:
        return category.replace("Recipes", "").strip().lower().replace(' ', '-')

# Get recipes for a specific category
def get_recipes_for_category(category_slug):
    URL = f'https://pinchofyum.com/recipes/{category_slug}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml')
        recipes = []
        recipe_elements = soup.find_all('h3')
        for recipe in recipe_elements:
            recipes.append(recipe.text.strip())
        return recipes
    else:
        return []

# Get recipe details for a specific dish
def get_recipe_details(dish_name):
    dish_slug = dish_name.strip().replace(" ", '-').lower()
    api_key = "7d03a1fbbac47877a5f875a9bebd96a76687c116a164c77310f85536d048a58d"  # Replace with your actual API key
    search = GoogleSearch({
        "q": dish_name,
        "api_key": api_key
    })
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'
    }
    result = search.get_dict()

    # Extract the first organic search result link
    first_result = result.get("organic_results", [{}])[0].get("link")
    URL=first_result              
    response=requests.get(URL,headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml')
        ingredients = []
        instructions = []
        
        # Get ingredients
        ingredients_section = soup.find('div', class_='tasty-recipes-ingredients')
        if ingredients_section:
            ing_list = ingredients_section.find_all('li')
            for item in ing_list:
                ingredients.append(item.text.strip())
        
        # Get instructions
        instructions_section = soup.find('div', class_='tasty-recipes-instructions')
        if instructions_section:
            instruction_list = instructions_section.find_all('li')
            for instruction in instruction_list:
                instructions.append(instruction.text.strip())
                
        # Try to get the recipe title
        title = dish_name  # Default to the provided dish name
        title_section = soup.find('h1', class_='tasty-recipes-title')
        if title_section:
            title = title_section.text.strip()
            
        # Try to get the recipe image
        image_url = URL
        a_tag = soup.find('a', class_='tasty-pins-banner-image-link')
    
        if a_tag:
        # Find the 'img' tag inside the 'a' tag
                img_tag = a_tag.find('img')
        
                if img_tag and 'src' in img_tag.attrs:
                    image_url = img_tag['src']
                else:
                    print("No image found inside the 'a' tag.")
        
            
        return {
            'title': title,
            'ingredients': ingredients,
            'instructions': instructions,
            'image_url': image_url
        }
    else:
        return None

# Flask routes
@app.route('/')
def index():
    response = get_url()
    if response:
        recipe_categories = scraping_homepage(response)
        return render_template('index.html', categories=recipe_categories)
    else:
        flash('Failed to connect to the recipe website.')
        return render_template('index.html', categories=[])

@app.route('/category/<category_name>')
def category(category_name):
    category_slug = process_category(category_name)
    recipes = get_recipes_for_category(category_slug)
    return render_template('category.html', 
                          category_name=category_name, 
                          recipes=recipes,
                          category_slug=category_slug)

@app.route('/recipe', methods=['GET', 'POST'])
def recipe():
    if request.method == 'POST':
        dish_name = request.form.get('dish_name')
        if not dish_name:
            flash('Please enter a dish name.')
            return redirect(url_for('index'))
            
        # URL encode the dish name before redirecting
        return redirect(url_for('recipe', dish_name=dish_name))
    
    else:
        dish_name = request.args.get('dish_name')
        if not dish_name:
            flash('Dish name not found.')
            return redirect(url_for('index'))
            
        recipe_details = get_recipe_details(dish_name)
        
        if recipe_details:
            return render_template('recipe.html', 
                                  dish_name=dish_name,
                                  recipe=recipe_details)
        else:
            flash(f'Could not find recipe for "{dish_name}".')
            return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001, debug=True)

    // JavaScript Code
    // Mock recipe data
        const mockRecipes = [
            {
                id: 1,
                title: "Spaghetti Carbonara",
                cook_time: "30 min",
                image: "https://images.unsplash.com/photo-1588013273468-315fd88ea34c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1169&q=80",
                link: "https://example.com/recipe1",
                ingredients: ["pasta", "eggs", "bacon", "cheese"],
                summary: "A classic Italian pasta dish with a creamy egg sauce, crispy bacon, and Parmesan cheese. Simple ingredients create an incredibly flavorful meal."
            },
            {
                id: 2,
                title: "Vegetable Stir Fry",
                cook_time: "20 min",
                image: "https://images.unsplash.com/photo-1512058564366-18510be2db19?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1172&q=80",
                link: "https://example.com/recipe2",
                ingredients: ["vegetables", "soy sauce", "rice", "oil"],
                summary: "Quick and healthy stir-fry with fresh vegetables in a savory sauce. Perfect for a weeknight dinner and highly customizable."
            },
            {
                id: 3,
                title: "Chocolate Chip Cookies",
                cook_time: "25 min",
                image: "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=764&q=80",
                link: "https://example.com/recipe3",
                ingredients: ["flour", "sugar", "chocolate chips", "butter", "eggs"],
                summary: "Classic chocolate chip cookies with crispy edges and chewy centers. These will become your go-to cookie recipe!"
            },
            {
                id: 4,
                title: "Greek Salad",
                cook_time: "15 min",
                image: "https://images.unsplash.com/photo-1540420773420-3366772f4999?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=684&q=80",
                link: "https://example.com/recipe4",
                ingredients: ["tomatoes", "cucumber", "olives", "feta cheese", "olive oil"],
                summary: "Fresh and vibrant Greek salad with crisp vegetables, briny olives, and creamy feta cheese. Dressed with a simple lemon-olive oil vinaigrette."
            },
            {
                id: 5,
                title: "Chicken Curry",
                cook_time: "45 min",
                image: "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=687&q=80",
                link: "https://example.com/recipe5",
                ingredients: ["chicken", "curry powder", "coconut milk", "onions", "garlic"],
                summary: "Aromatic and flavorful chicken curry with tender pieces of chicken in a rich, spiced coconut sauce. Serve with rice or naan bread."
            },
            {
                id: 6,
                title: "Avocado Toast",
                cook_time: "10 min",
                image: "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=687&q=80",
                link: "https://example.com/recipe6",
                ingredients: ["avocado", "bread", "lemon juice", "salt", "pepper"],
                summary: "Simple yet delicious avocado toast topped with a sprinkle of seasonings. A perfect healthy breakfast or snack that's ready in minutes."
            }
        ];

        // Mock favorite recipes
        const mockFavorites = [
            mockRecipes[0], // Spaghetti Carbonara
            mockRecipes[2], // Chocolate Chip Cookies
            mockRecipes[4]  // Chicken Curry
        ];

        // User favorites 
        let userFavorites = JSON.parse(localStorage.getItem('recipeFavorites')) || [];

        // Currently displayed recipes (either API results or mock)
        let displayedRecipes = [...mockRecipes];

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function(){
            displayRecipes(displayedRecipes);
            displayHomeFavorites();
            displayFavorites();
            attachEventListeners();
        });

        // Display recipes in the home section
        function displayRecipes(recipes){
            const recipesGrid = document.getElementById('recipes-grid');
            recipesGrid.innerHTML = '';

            if (recipes.length === 0){
                recipesGrid.innerHTML = '<div class="no-results">No recipes found with those ingredients. Try different search terms.</div>';
                return;
            }

            // Show only 3 recipes 
            const recipesToShow = recipes.slice(0, 3);

            recipesToShow.forEach(recipe => {
                const isFavorite = userFavorites.some(fav => fav.id === recipe.id);
                const recipeCard = createRecipeCard(recipe, isFavorite);
                recipesGrid.appendChild(recipeCard);
            });
            attachFavoriteListeners();
        }

        // Display the favorites in home Section
        function displayHomeFavorites(){
            const homeFavoritesContainer = document.getElementById('home-favorites-container');
            homeFavoritesContainer.innerHTML = '';

            if (userFavorites.length === 0 ){
                homeFavoritesContainer.innerHTML='<div class="no-favorites">You haven\'t added any favorites yet. Browse recipes and favorite them</div>';
                return;
            }

            // Show up to 3 favorites
            const favoritesToShow = userFavorites.slice(0, 3);

            favoritesToShow.forEach(recipe => {
                const recipeCard = createRecipeCard(recipe, true);
                homeFavoritesContainer.appendChild(recipeCard);
            });
            attachRemoveFavoriteListeners();
        }

        // Display favorites in favorites section 
        function displayFavorites() {
            const favoritesContainer = document.getElementById('favorites-container');
            favoritesContainer.innerHTML = '';
            
            if (userFavorites.length === 0) {
                favoritesContainer.innerHTML = '<div class="no-favorites">You haven\'t added any favorites yet. Browse recipes and click the heart to save them!</div>';
                return;
            }
            
            userFavorites.forEach(recipe => {
                const recipeCard = createRecipeCard(recipe, true);
                favoritesContainer.appendChild(recipeCard);
            });
            
            attachRemoveFavoriteListeners();
        }

        // Create a recipe card element
        function createRecipeCard(recipe, isFavorite) {
            const flipCard = document.createElement('div');
            flipCard.className = 'flip-card';
            // add data-id so we can find cards by recipe id later
            if (recipe && recipe.id !== undefined) {
                flipCard.setAttribute('data-id', recipe.id);
            }

            // truncate summary for display to ~30 words
            const displaySummary = truncateWords(recipe.summary || '', 30);
            
            const favoriteButton = isFavorite ? 
                `<button class="remove-favorite-btn" data-id="${recipe.id}">
                    <span class="heart-icon"><i class="fas fa-heart"></i></span> Remove from Favorites
                </button>` :
                `<button class="favorite-btn" data-id="${recipe.id}">
                    <span class="heart-icon"><i class="far fa-heart"></i></span> Add to Favorites
                </button>`;
            
            flipCard.innerHTML = `
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div class="recipe-image">
                            <img src="${recipe.image}" alt="${recipe.title}">
                        </div>

                        <div class="recipe-info">
                        <h3 class="recipe-title">${recipe.title}</h3>

                            <div class="recipe-meta">

                            <p><i class="fas fa-fire"></i> 
  ${recipe.calories 
      ? `${recipe.calories} cal${recipe.servings ? ' • ' + Math.round(recipe.calories / recipe.servings) + ' per serving' : ''}` 
      : ''}
</p>


                                    ${recipe.cook_time && recipe.cook_time !== 'Cook time not available' ? 
                                `<p><i class="far fa-clock"></i> ${recipe.cook_time}</p>` : ''}
                            </div>

                        </div>
                        <br>
                        <div class="flip-hint">Hover to see details</div>
                    </div>
                    <div class="flip-card-back">
                        <h3 class="recipe-title">${recipe.title}</h3>
                        <p class="cook-time"><i class="far fa-clock"></i> ${recipe.cook_time}</p>
                        <div class="recipe-summary">
                            <p>${displaySummary}</p>
                        </div>
                        <a href="${recipe.link}" class="recipe-link" target="_blank">
                            <i class="fas fa-external-link-alt"></i> View Full Recipe
                        </a>
                        ${favoriteButton}
                    </div>
                </div>
            `;
            
            return flipCard;
        }

        // Attach Event Listeners
        function attachEventListeners(){
            // Navigation Functionality 
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', function(e){
                    const section = this.getAttribute('data-section');
                    const sectionId = section ? section + '-section' : null;
                    const targetSection = sectionId ? document.getElementById(sectionId) : null;

                    // If the target section exists, perform single-page navigation. Otherwise allow normal navigation.
                    if (targetSection) {
                        e.preventDefault();

                        // Update nav link active state
                        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                        this.classList.add('active');

                        // Show corresponding section
                        document.querySelectorAll('.content-section').forEach(sectionEl => {
                            sectionEl.classList.remove('active');
                        });
                        targetSection.classList.add('active');
                        // Optionally scroll to top of the content
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                });
            });

            // Search functionality 
            document.getElementById('search-form').addEventListener('submit', function(e){
                e.preventDefault();
                const ingredients = document.getElementById('ingredient-input').value.trim();

                // If empty, show mock data
                if(!ingredients){
                    displayedRecipes = [...mockRecipes];
                    displayRecipes(displayedRecipes);
                    return;
                }

                // Build query and call Flask backend
                const params = new URLSearchParams({ ingredients });
                const url = `/search_recipes?${params.toString()}`;

                const recipesGrid = document.getElementById('recipes-grid');
                recipesGrid.innerHTML = '<div class="loading">Searching recipes...</div>';

            //     fetch(url)
            //         .then(res => res.json())
            //         .then(data => {
            //             if (data.error) {
            //                 recipesGrid.innerHTML = `<div class="no-results">Error: ${data.error}</div>`;
            //                 return;
            //             }

            //             // Map API results to UI shape
            //             const results = Array.isArray(data) ? data : [];
            //             displayedRecipes = results.map(r => ({
            //                 id: r.id,
            //                 title: r.title || r.name || 'Untitled',
            //                 cook_time: r.readyInMinutes ? `${r.readyInMinutes} min` : (r.cook_time || 'N/A'),
            //                 image: r.image || '',
            //                 link: r.sourceUrl || r.spoonacularSourceUrl || '#',
            //                 ingredients: (r.extendedIngredients || []).map(i => i.name) || [],
            //                 summary: r.summary ? stripHtml(r.summary) : (r.description || '')
            //             }));

            //             if(displayedRecipes.length === 0){
            //                 recipesGrid.innerHTML = '<div class="no-results">No recipes found with those ingredients. Try different search terms.</div>';
            //                 return;
            //             }

            //             displayRecipes(displayedRecipes);
            //         })
            //         .catch(err => {
            //             recipesGrid.innerHTML = `<div class="no-results">Error: ${err.message}</div>`;
            //         });
            // });
            fetch(url)
            .then(res => {
                if (!res.ok) {
                    // Handle non-2xx responses by trying to parse the error message
                    return res.json().then(err => { throw new Error(err.error || `Request failed with status ${res.status}`) });
                }
                return res.json();
            })
            .then(data => {
                // Edamam returns the recipes in an array (already handled by your backend)
                const results = Array.isArray(data) ? data : [];
                
// NEW MAPPING FOR EDAMAM API  (drop-in replacement)
displayedRecipes = results.map(r => {
  // works whether backend returns {recipe: {...}} or a flat {...}
  const recipe = r?.recipe ?? r;

  // extract Edamam id
  const getRecipeId = (uri) => {
    if (!uri) return null;
    const parts = uri.split('#recipe_');
    return parts.length > 1 ? parts[1] : null;
  };

  const recipeId = getRecipeId(recipe?.uri);

  return {
    id: recipeId,
    title: recipe?.label || recipe?.title || 'Untitled Recipe',

    calories: typeof recipe?.calories === 'number' ? Math.round(recipe.calories) : null,
    servings: recipe?.yield || null,

    cook_time:
        recipe?.totalTime && recipe.totalTime !== 0
        ? `${recipe.totalTime} min`
        : (recipe?.cookTime || recipe?.total_time || ''),
    image: recipe?.image || 'https://via.placeholder.com/400x300.png?text=No+Image',
    link: recipe?.url || recipe?.link || '#',
    ingredients: recipe?.ingredientLines || recipe?.ingredients || [],
    summary: recipe?.ingredientLines
      ? recipe.ingredientLines.slice(0, 4).join(', ')
      : (recipe?.summary || 'No summary available.')
  };
}).filter(r => r.id);


                if (displayedRecipes.length === 0) {
                    recipesGrid.innerHTML = '<div class="no-results">No recipes found. Try different ingredients!</div>';
                    return;
                }

                displayRecipes(displayedRecipes);
            })
            .catch(err => {
                recipesGrid.innerHTML = `<div class="no-results">An error occurred: ${err.message}</div>`;
                console.error("Search failed:", err);
            });
        });
    }

        // Add to favorites function
        function attachFavoriteListeners(){
            document.querySelectorAll('.favorite-btn').forEach(button => {
                button.addEventListener('click', function(e){
                    e.stopPropagation();  // Prevents card flip

                    const recipeId = parseInt(this.getAttribute('data-id'));
                    // Look up in currently displayed recipes first, then fallback to mock or favorites
                    let recipe = displayedRecipes.find(r => r.id === recipeId) || mockRecipes.find(r => r.id === recipeId) || userFavorites.find(r => r.id === recipeId);

                    if(recipe && !userFavorites.some(fav => fav.id === recipeId)){
                        userFavorites.push(recipe);
                        localStorage.setItem('recipeFavorites', JSON.stringify(userFavorites));

                        // Update the button
                        this.innerHTML ='<span class="heart-icon"><i class="fas fa-heart"></i></span> Remove from Favorites';
                        this.className = 'remove-favorite-btn';

                        // Update favorites on home
                        displayHomeFavorites();

                        // Update favorites section if we're on that page 
                        if (document.getElementById('favorites-section').classList.contains('active')){
                            displayFavorites();
                        }

                        // Reattach event listeners
                        attachRemoveFavoriteListeners();
                    }
                });
            });
        }

        // Remove from favorites functionality 
        function attachRemoveFavoriteListeners(){
            document.querySelectorAll('.remove-favorite-btn').forEach(button => {
                button.addEventListener('click', function(e){
                    e.stopPropagation();  // Prevent card flip
                    const recipeId = parseInt(this.getAttribute('data-id'));
                    userFavorites = userFavorites.filter(fav => fav.id !== recipeId);

                    localStorage.setItem('recipeFavorites', JSON.stringify(userFavorites));

                    // Update favorites on home page
                    displayHomeFavorites();

                    // If we are on favorites page, remove the card
                    if(document.getElementById('favorites-section').classList.contains('active')){
                        displayFavorites();
                    }

                    // If we're on the home page, update the button
                    if (document.getElementById('home-section').classList.contains('active')){
                        // Find card in recipe suggestions
                        const recipeCard = document.querySelector(`.flip-card[data-id="${recipeId}"]`);

                        if (recipeCard) {
                            const button = recipeCard.querySelector('.remove-favorite-btn');
                            if(button){
                                button.innerHTML = '<span class="heart-icon"><i class="far fa-heart"></i></span> Add to Favorites';
                                button.className = 'favorite-btn';
                                attachFavoriteListeners();
                            }
                        }
                    }
                });
            });
        }

        // Helper to strip HTML tags (Spoonacular returns HTML in summaries)
        function stripHtml(html){
            const tmp = document.createElement('div');
            tmp.innerHTML = html || '';
            return tmp.textContent || tmp.innerText || '';
        }

        // Helper to truncate text to a number of words
        function truncateWords(text, wordLimit){
            if(!text) return '';
            const words = text.split(/\s+/).filter(Boolean);
            if(words.length <= wordLimit) return words.join(' ');
            return words.slice(0, wordLimit).join(' ') + '...';
        }




// autocomplete
const ingredientInput = document.getElementById("ingredient-input");

//dropdown box
const suggestionBox = document.createElement("ul");
suggestionBox.className = "autocomplete-list";
ingredientInput.parentNode.appendChild(suggestionBox);

let activeIndex = -1;

ingredientInput.addEventListener("input", async () => {
  const query = ingredientInput.value.trim();
  suggestionBox.innerHTML = "";
  suggestionBox.classList.remove("show");
  activeIndex = -1;

  if (query.length < 2) return;

  try {
    const res = await fetch(`/autocomplete?query=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (!Array.isArray(data) || data.length === 0) return;

    suggestionBox.classList.add("show");

    data.slice(0, 5).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item.name;
      li.addEventListener("click", () => {
        ingredientInput.value = item.name;
        suggestionBox.innerHTML = "";
        suggestionBox.classList.remove("show");
      });
      suggestionBox.appendChild(li);
    });

    //match dropdown width to input
    const rect = ingredientInput.getBoundingClientRect();
    suggestionBox.style.width = rect.width + "px";
  } catch (err) {
    console.error("Autocomplete error:", err);
  }
});

// --- Keyboard navigation ---
ingredientInput.addEventListener("keydown", (e) => {
  const items = suggestionBox.querySelectorAll("li");
  if (!items.length) return;

  switch (e.key) {
    case "ArrowDown":
      e.preventDefault();
      activeIndex = (activeIndex + 1) % items.length;
      updateActive(items);
      break;
    case "ArrowUp":
      e.preventDefault();
      activeIndex = (activeIndex - 1 + items.length) % items.length;
      updateActive(items);
      break;
    case "Enter":
    case "Tab":
      if (activeIndex >= 0 && activeIndex < items.length) {
        e.preventDefault();
        ingredientInput.value = items[activeIndex].textContent;
        suggestionBox.innerHTML = "";
        suggestionBox.classList.remove("show");
      }
      break;
    case "Escape":
      suggestionBox.innerHTML = "";
      suggestionBox.classList.remove("show");
      activeIndex = -1;
      break;
  }
});

function updateActive(items) {
  items.forEach((item, i) => {
    item.classList.toggle("active", i === activeIndex);
  });
}

document.addEventListener("click", (e) => {
  if (!suggestionBox.contains(e.target) && e.target !== ingredientInput) {
    suggestionBox.innerHTML = "";
    suggestionBox.classList.remove("show");
  }
});

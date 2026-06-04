const USER_ID = "default";

async function loadBasket() {
    const res = await fetch(`/basket?user_id=${USER_ID}`);
    const basket = await res.json();

    const container = document.getElementById("basket");

    container.innerHTML = `
        ${basket.map(item => `
            <div class="basket-item">
                <strong>${item.name}</strong><br><br>

                <div class="quantity-row">
                    <label>Grams / ml:</label>

                    <input
                        type="number"
                        min="0"
                        value="${item.quantity}"
                        onkeydown="if(event.key === 'Enter') changeQuantity('${item.product_id}', this.value)"
                    >

                    <button onclick="removeProduct('${item.product_id}')">
                        Remove
                    </button>
                </div>
            </div>
        `).join("")}

        <button class="clear-basket-btn" onclick="clearBasket()">
            Clear basket
        </button>
    `;

    loadTotals();
}

async function changeQuantity(productId, quantity) {
    if (quantity < 0) {
        alert("Quantity cannot be negative. Setting it to 0.");
        quantity = 0;
    }

    await fetch("/basket", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_id: USER_ID,
            product_id: productId,
            quantity: quantity
        })
    });

    loadBasket();
}


async function removeProduct(productId) {    
    await fetch(
        `/basket?user_id=${USER_ID}&product_id=${productId}`,
        { method: "DELETE" }
    );

    loadBasket();
}

async function loadTotals() {
    
    const res = await fetch(`/totals?user_id=${USER_ID}`);
    const totals = await res.json();

    document.getElementById("totals").innerHTML = `
        <div class="totals-grid">
            <span>Calories 🔥: ${Math.round(totals.energy_kcal)} kcal</span>
            <span>Proteins 🥩: ${Math.round(totals.protein_g)} g</span>
            <span>Carbs 🍞: ${Math.round(totals.carbs_g)} g</span>
            <span>Fats 🥑: ${Math.round(totals.fat_g)} g</span>
        </div>
    `;
}


async function searchProducts(query) {
    
    if (!query) {
        document.getElementById("searchResults").innerHTML = "";
        return;
    }

    const res = await fetch(
        `/products/search?q=${encodeURIComponent(query)}`
    );

    const products = await res.json();

    document.getElementById("searchResults").innerHTML =
        products.map(product => `
            <div class="result">
                <div class="result-name">
                    ${product.name}
                </div>

                <button onclick="addProduct('${product.id}')">
                    Add
                </button>
            </div>
        `).join("");
}


async function addProduct(productId) {
    
    await fetch("/basket", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_id: USER_ID,
            product_id: productId,
            quantity: 100
        })
    });

    document.getElementById("searchInput").value = "";
    document.getElementById("searchResults").innerHTML = "";

    loadBasket();
}


async function clearBasket() {

    if (!confirm("Clear entire basket?")) return;
    
    await fetch(`/basket/clear?user_id=${USER_ID}`, {
        method: "DELETE"
    });

    loadBasket();
}


document.addEventListener("focusin", (e) => {
    if (e.target.matches(".basket-item input[type='number']")) {
        e.target.select();
    }
});


document
    .getElementById("searchInput")
    .addEventListener("input", (e) => {
        searchProducts(e.target.value);
    });

loadBasket();
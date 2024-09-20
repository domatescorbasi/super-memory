document.addEventListener('DOMContentLoaded', function () {
    fetchFoodItems();
    setupFormSubmitHandler();

     // Set up button click handlers for calculator functionality

});

function calculateTotalCost() {
    fetch('/api/calculate-total-cost')
        .then(response => response.json())
        .then(data => {
            let totalCostDiv = document.getElementById('total-cost');
            totalCostDiv.innerHTML = ''; // Clear previous content

            // Display the total cost
            totalCostDiv.innerHTML = `<div class="alert alert-info mt-3">
                <strong>Total Cost:</strong> $${data.total_cost.toFixed(2)}
            </div>`;

            let detailsDiv = document.getElementById('cost-details');
            detailsDiv.innerHTML = '<h5>Cost Breakdown:</h5>';

            // Iterate over the details object and display the breakdown
            Object.keys(data.details).forEach(macronutrient => {
                const item = data.details[macronutrient]; // Access each macronutrient's details
                const gramsNeeded = item.grams_needed; // Grams of the macronutrient needed

                detailsDiv.innerHTML += `<div><strong>${macronutrient}:</strong> ${item.food} - 
                    ${item.total_weight.toFixed(2)}g (to meet ${gramsNeeded}g), $${item.cost.toFixed(2)}</div>`;
            });
        })
        .catch(error => showToast(error + ' Error calculating total cost', 'danger'));
}



function fetchFoodItems() {
    fetch('/api/food-items')
        .then(response => response.json())
        .then(data => {
            let foodItemsDiv = document.getElementById('food-items');
            foodItemsDiv.innerHTML = ''; // Clear previous content
            const isDarkMode = document.body.classList.contains('bg-dark');

            data.forEach(item => {
                const textClass = isDarkMode ? 'text-light' : 'text-dark';
                const iconClass = 'fas'; // Base class for FontAwesome icons

                foodItemsDiv.innerHTML += `
                    <div class="w-auto card-body">
                        <ul class="list-group list-group-horizontal">
                            <li class="list-group-item flex-fill ${textClass}">
                                <h5 class="card-title ${textClass} d-none d-sm-block">${item.name}</h5>
                                <i class="fas fa-tag d-block d-sm-none" style="color: #888;" 
                                   data-bs-toggle="tooltip" 
                                   data-bs-placement="top" 
                                   title="${item.name}"></i>
                            </li>
                            <li class="list-group-item flex-fill ${textClass}" 
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top" 
                                title="Protein: ${item.protein}g">
                                <i class="${iconClass} fa-drumstick-bite" style="color: #D2691E;"></i>
                                <span class="d-none d-sm-inline"> Protein: ${item.protein}g</span>
                            </li>
                            <li class="list-group-item flex-fill ${textClass}" 
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top" 
                                title="Fat: ${item.fat}g">
                                <i class="${iconClass} fa-gas-pump" style="color: #FFD700;"></i>
                                <span class="d-none d-sm-inline"> Fat: ${item.fat}g</span>
                            </li>
                            <li class="list-group-item flex-fill ${textClass}" 
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top" 
                                title="Carb: ${item.carb}g">
                                <i class="${iconClass} fa-bolt" style="color: #F4A460;"></i>
                                <span class="d-none d-sm-inline"> Carb: ${item.carb}g</span>
                            </li>
                            <li class="list-group-item flex-fill ${textClass}" 
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top" 
                                title="Price: ${item.price_per_unit}">
                                <i class="${iconClass} fa-dollar-sign" style="color: #37f31a;"></i>
                                <span class="d-none d-sm-inline"> Price: ${item.price_per_unit}</span>
                            </li>
                            <li class="list-group-item flex-fill ${textClass}" 
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top" 
                                title="Weight: ${item.unit_weight}g">
                                <i class="${iconClass} fa-weight-hanging" style="color: #6f7db6;"></i>
                                <span class="d-none d-sm-inline"> ${item.unit_weight}g</span>
                            </li>
                            <li class="list-group-item flex-fill d-flex justify-content-center align-items-center">
                                <div class="d-flex flex-column flex-sm-row btn-group">
                                    <button class="btn btn-warning btn-sm" onclick="editFoodItem(${item.id})">
                                        <i class="fa-solid fa-edit"></i> Edit
                                    </button>
                                    <button class="btn btn-primary btn-sm" onclick="copyToAddForm(${item.id})">
                                        <i class="fa-solid fa-copy"></i> Copy
                                    </button>
                                    <button class="btn btn-danger btn-sm" onclick="deleteFoodItem(${item.id})">
                                        <i class="fa-solid fa-trash-can"></i> Delete
                                    </button>
                                </div>
                            </li>
                        </ul>
                    </div>`;
            });

            // Initialize Bootstrap tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        })
        .catch(error => console.error('Error fetching food items:', error));
}


function deleteFoodItem(itemId) {
    fetch(`/api/food-items/${itemId}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (response.ok) {
                showToast('Food item deleted successfully', 'success');
                fetchFoodItems(); // Refresh the list
            } else {
                response.json().then(data => showToast(data.message, 'danger'));
            }
        })
        .catch(error => console.error('Error deleting food item:', error));
}

function setupFormSubmitHandler() {
    const form = document.getElementById('food-form');

    // Remove existing event listener
    form.removeEventListener('submit', handleFormSubmit);

    // Add new event listener based on the current mode
    form.addEventListener('submit', handleFormSubmit);
}

function handleFormSubmit(event) {
    event.preventDefault(); // Prevent form submission

    const itemId = document.getElementById('item_id').value;
    const foodData = {
        name: document.getElementById('name').value,
        protein: parseFloat(document.getElementById('protein').value),
        fat: parseFloat(document.getElementById('fat').value),
        carb: parseFloat(document.getElementById('carb').value),
        price_per_unit: parseFloat(document.getElementById('price_per_unit').value),
        unit_weight: parseFloat(document.getElementById('unit_weight').value)
    };

    if (itemId) {
        // Editing an existing food item
        fetch(`/api/edit-food-item/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(foodData)
        })
            .then(response => response.json())
            .then(data => {
                showToast(data.message, 'success');
                resetForm();
                fetchFoodItems();
            })
            .catch(error => showToast('Error editing food item', 'danger'));
    } else {
        // Adding a new food item
        fetch('/api/add-food-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(foodData)
        })
            .then(response => response.json())
            .then(data => {
                showToast(data.message, 'success');
                resetForm();
                fetchFoodItems();
            })
            .catch(error => showToast('Error adding food item', 'danger'));
    }
}

function editFoodItem(itemId) {
    fetch(`/api/food-items/${itemId}`)
        .then(response => response.json())
        .then(item => {
            document.getElementById('item_id').value = item.id;
            document.getElementById('name').value = item.name;
            document.getElementById('protein').value = item.protein;
            document.getElementById('fat').value = item.fat;
            document.getElementById('carb').value = item.carb;
            document.getElementById('price_per_unit').value = item.price_per_unit;
            document.getElementById('unit_weight').value = item.unit_weight;

            document.getElementById('form-heading').innerText = 'Edit Food Item';
            document.getElementById('submit-btn').innerHTML = '<i class="fas fa-save"></i> Save Changes';
        })
        .catch(error => console.error('Error fetching food item:', error));
}

function resetForm() {
    document.getElementById('item_id').value = '';
    document.getElementById('name').value = '';
    document.getElementById('protein').value = '';
    document.getElementById('fat').value = '';
    document.getElementById('carb').value = '';
    document.getElementById('price_per_unit').value = '';
    document.getElementById('unit_weight').value = '';

    document.getElementById('form-heading').innerText = 'Add Food Item';
    document.getElementById('submit-btn').innerHTML = '<i class="fas fa-plus"></i> Add Food Item';
}

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    const toastHTML = `
        <div class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>`;

    toastContainer.innerHTML += toastHTML;

    // Initialize the toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}


// Calculate costs of macronutrients for all items
function calculateCosts() {
    fetch('/api/calculate-costs')
        .then(response => response.json())
        .then(data => {
            let costsDiv = document.getElementById('calculated-costs');
            costsDiv.innerHTML = ''; // Clear previous content
            data.forEach(item => {
                costsDiv.innerHTML += `<div class="alert alert-info mt-3">
                    <strong>${item.name}</strong>: 
                    Protein cost: ${item.protein_cost}, 
                    Fat cost: ${item.fat_cost}, 
                    Carb cost: ${item.carb_cost}
                </div>`;
            });
        })
        .catch(error => showToast('Error calculating costs', 'danger'));
}

// Find the cheapest macronutrient source
function findCheapest() {
    let macronutrient = document.getElementById('macronutrient-select').value;

    fetch(`/api/cheapest-macronutrient?macronutrient=${macronutrient}`)
        .then(response => response.json())
        .then(data => {
            let cheapestDiv = document.getElementById('cheapest-macronutrient');
            cheapestDiv.innerHTML = `<div class="alert alert-success mt-3">
                Cheapest ${macronutrient}: ${data.cheapest_item} at ${data.cost_per_gram} per gram
            </div>`;
        })
        .catch(error => showToast('Error finding cheapest macronutrient', 'danger'));
}

const animateElements = document.querySelectorAll('.animate');

animateElements.forEach((element, index) => {
    setTimeout(() => {
        element.classList.add('show');
    }, index * 150);
});

function copyToAddForm(itemId) {
    fetch(`/api/food-items/${itemId}`)
        .then(response => response.json())
        .then(item => {
            document.getElementById('item_id').value = ''; // Clear ID since it's a new form
            document.getElementById('name').value = item.name;
            document.getElementById('protein').value = item.protein;
            document.getElementById('fat').value = item.fat;
            document.getElementById('carb').value = item.carb;
            document.getElementById('price_per_unit').value = item.price_per_unit;
            document.getElementById('unit_weight').value = item.unit_weight;

            document.getElementById('form-heading').innerText = 'Add Food Item';
            document.getElementById('submit-btn').innerHTML = '<i class="fas fa-plus"></i> Add Food Item';
        })
        .catch(error => console.error('Error copying food item to form:', error));
}

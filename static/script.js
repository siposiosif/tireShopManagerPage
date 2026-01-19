document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const serviceSelector = document.getElementById('service-selector');
    const addServiceBtn = document.getElementById('add-service-btn');
    const selectedServicesDisplay = document.getElementById('selected-services-display');
    const selectedServicesInput = document.getElementById('selected-services');
    const selectedServicesList = document.getElementById('selected-services-list');
    const totalPrice = document.getElementById('total-price');
    const priceSection = document.getElementById('price-section');

    let allServices = [];
    let selectedServices = [];

    // Service prices (fallback for default services)
    const defaultPrices = {
        'tire-change': 150,
        'balancing': 50
    };

    // Function to update price display and visibility
    function updatePriceDisplay() {
        selectedServicesList.innerHTML = '';
        let total = 0;
        let hasPricedServices = false;

        if (selectedServices.length === 0) {
            // Hide price section when no services selected
            priceSection.style.display = 'none';
            selectedServicesInput.value = '';
            return;
        }

        // Show price section when services are selected
        priceSection.style.display = 'block';

        selectedServices.forEach(serviceId => {
            const service = allServices.find(s => s.id === serviceId);
            if (service && service.price > 0) {
                hasPricedServices = true;
                total += service.price;

                const serviceRow = document.createElement('div');
                serviceRow.className = 'price-row';
                serviceRow.innerHTML = `
                    <span class="price-label">${service.name}:</span>
                    <span class="price-value">${service.price} RON</span>
                `;
                selectedServicesList.appendChild(serviceRow);
            }
        });

        // If no priced services, hide the price section
        if (!hasPricedServices) {
            priceSection.style.display = 'none';
        }

        totalPrice.textContent = `${total} RON`;
        selectedServicesInput.value = selectedServices.join(',');
    }

    // Function to update selected services display
    function updateSelectedServicesDisplay() {
        selectedServicesDisplay.innerHTML = '';

        if (selectedServices.length === 0) {
            selectedServicesDisplay.innerHTML = '<p class="no-services">Niciun serviciu selectat. Adăugați servicii folosind butonul "+" de mai jos.</p>';
            return;
        }

        selectedServices.forEach(serviceId => {
            const service = allServices.find(s => s.id === serviceId);
            if (service) {
                const serviceItem = document.createElement('div');
                serviceItem.className = 'selected-service-item';

                const serviceInfo = document.createElement('div');
                serviceInfo.className = 'selected-service-info';
                serviceInfo.textContent = `${service.name} (${service.duration} min)`;

                const servicePrice = document.createElement('span');
                servicePrice.className = 'selected-service-price';
                servicePrice.textContent = service.price > 0 ? `${service.price} RON` : 'Fără preț';

                const removeBtn = document.createElement('button');
                removeBtn.className = 'remove-service-btn';
                removeBtn.textContent = '✕';
                removeBtn.onclick = () => removeService(serviceId);

                serviceItem.appendChild(serviceInfo);
                serviceItem.appendChild(servicePrice);
                serviceItem.appendChild(removeBtn);

                selectedServicesDisplay.appendChild(serviceItem);
            }
        });
    }

    // Function to add a service
    function addService(serviceId) {
        if (!serviceId || selectedServices.includes(serviceId)) {
            return; // Don't add if already selected or empty
        }

        selectedServices.push(serviceId);
        updateSelectedServicesDisplay();
        updatePriceDisplay();
        updateTimeSlots();

        // Reset selector
        serviceSelector.value = '';
        addServiceBtn.disabled = true;
    }

    // Function to remove a service
    function removeService(serviceId) {
        selectedServices = selectedServices.filter(id => id !== serviceId);
        updateSelectedServicesDisplay();
        updatePriceDisplay();
        updateTimeSlots();
    }

    // Function to populate service selector
    function populateServiceSelector(services) {
        serviceSelector.innerHTML = '<option value="">Selectați un serviciu...</option>';

        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} (${service.duration} min) - ${service.price > 0 ? service.price + ' RON' : 'Fără preț'}`;
            serviceSelector.appendChild(option);
        });
    }

    // Load available services
    fetch('/api/services')
        .then(res => res.json())
        .then(services => {
            allServices = services;
            populateServiceSelector(services);
            updateSelectedServicesDisplay();
            updatePriceDisplay();
        })
        .catch(err => {
            console.log('Could not load services, using defaults');
            // Create default services
            allServices = [
                { id: 'tire-change', name: 'Schimb Anvelope Sezonier', duration: 60, price: 200 },
                { id: 'balancing', name: 'Echilibrare Roți', duration: 30, price: 50 }
            ];
            populateServiceSelector(allServices);
            updateSelectedServicesDisplay();
            updatePriceDisplay();
        });

    const allHours = [
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30",
    ];

    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);

    function updateTimeSlots() {
        const selectedDate = dateInput.value;

        if (!selectedDate || selectedServices.length === 0) {
            timeSelect.disabled = true;
            timeSelect.innerHTML = '<option value="">Selectați data și adăugați servicii...</option>';
            return;
        }

        timeSelect.disabled = false;
        timeSelect.innerHTML = '<option value="">Se verifică disponibilitatea...</option>';

        // Calculate total duration of selected services
        let totalDuration = 0;
        selectedServices.forEach(serviceId => {
            const service = allServices.find(s => s.id === serviceId);
            if (service) {
                totalDuration += service.duration;
            }
        });

        fetch(`/get_slots?date=${selectedDate}&services=${selectedServices.join(',')}&duration=${totalDuration}`)
            .then(res => res.json())
            .then(slotData => {
                timeSelect.innerHTML = '<option value="">Selectați Ora</option>';
                
                // Check if selectedDate is today or in the past
                const today = new Date().toISOString().split('T')[0];
                const isTodayOrPast = selectedDate <= today;
                
                allHours.forEach(hour => {
                    const option = document.createElement('option');
                    option.value = hour;
                    
                    if (isTodayOrPast) {
                        // For today/past: slotData contains taken/unavailable slots
                        if (slotData.includes(hour)) {
                            option.textContent = `${hour} (Ocupat)`;
                            option.disabled = true;
                            option.style.color = "#666";
                        } else {
                            option.textContent = `${hour} (Liber)`;
                        }
                    } else {
                        // For future dates: slotData contains available slots
                        if (slotData.includes(hour)) {
                            option.textContent = `${hour} (Liber)`;
                        } else {
                            option.textContent = `${hour} (Ocupat)`;
                            option.disabled = true;
                            option.style.color = "#666";
                        }
                    }
                    
                    timeSelect.appendChild(option);
                });
            });
    }

    // Event listeners
    dateInput.addEventListener('change', updateTimeSlots);

    serviceSelector.addEventListener('change', function() {
        addServiceBtn.disabled = !this.value;
    });

    addServiceBtn.addEventListener('click', function() {
        const selectedServiceId = serviceSelector.value;
        if (selectedServiceId) {
            addService(selectedServiceId);
        }
    });

    // Initialize
    updateSelectedServicesDisplay();
    updatePriceDisplay();
});

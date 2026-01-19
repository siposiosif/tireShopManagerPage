document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');

    if (!dateInput || !timeSelect) {
        return;
    }

    const allHours = [
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30",
    ];

    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);

    dateInput.addEventListener('change', function () {
        const selectedDate = this.value;
        if (!selectedDate) {
            return;
        }

        timeSelect.disabled = false;
        timeSelect.innerHTML = '<option value="">Se verifică disponibilitatea...</option>';

        fetch(`/get_slots?date=${selectedDate}`)
            .then(res => res.json())
            .then(takenSlots => {
                timeSelect.innerHTML = '<option value="">Selectați Ora</option>';
                allHours.forEach(hour => {
                    const option = document.createElement('option');
                    option.value = hour;
                    if (takenSlots.includes(hour)) {
                        option.textContent = `${hour} (Ocupat)`;
                        option.disabled = true;
                        option.style.color = "#666";
                    } else {
                        option.textContent = `${hour} (Liber)`;
                    }
                    timeSelect.appendChild(option);
                });
            });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const slotButtons = document.querySelectorAll(".slot-btn");

    slotButtons.forEach(button => {
        button.addEventListener("click", () => {
            const slotId = button.dataset.slotId;
            const ticketId = button.dataset.ticketId;

            fetch(`/choose_slot/${slotId}/${ticketId}`)
                .then(response => response.text())
                .then(data => {
                    alert(data);
                    location.reload();
                })
                .catch(error => {
                    console.error("Error assigning slot:", error);
                });
        });
    });
});

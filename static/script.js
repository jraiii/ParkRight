function togglePassword(id) {
  const field = document.getElementById(id);
  field.type = field.type === "password" ? "text" : "password";
}

document.addEventListener("DOMContentLoaded", () => {
  const slots = document.querySelectorAll(".slot.available");
  slots.forEach(slot => {
    slot.addEventListener("click", () => {
      alert(`You selected slot ${slot.textContent}. Please login or signup to reserve.`);
      window.location.href = "/login";
    });
  });
});

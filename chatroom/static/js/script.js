const dropdownButton = document.querySelector("#dropdown-button");
const dropdownMenu = document.querySelector(".dropdown-menu");

if (dropdownButton) {
  dropdownButton.addEventListener("click", (e) => {
    dropdownMenu.classList.toggle("show");
  });
}

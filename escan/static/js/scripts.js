/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project
document.addEventListener("DOMContentLoaded", function() {
  const burger = document.querySelector(".burger");
  const menu = document.querySelector(".menu");

  burger.addEventListener("click", function() {
      menu.classList.toggle("show");
  });
});

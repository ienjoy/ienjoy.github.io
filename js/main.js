// Get references to HTML elements
const weatherContainer = document.getElementById("weather");
const cityName = document.getElementById("cityName");
const select = document.getElementById("citySelect");
const fetchButton = document.getElementById("fetchWeatherButton");
const swiperContainer = document.querySelector(".swiper-container"); // Reference to Swiper container

// Variable to store city data
let cityData;

// Initialize Swiper
var swiper = new Swiper(".swiper-container", {
  direction: "horizontal",
  spaceBetween: 15,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  watchSlidesProgress: true,
  breakpoints: {
    640: {
      slidesPerView: 2,
    },
    992: {
      slidesPerView: 3.5,
    },
  },
});

// Event listener for the fetch button click
fetchButton.addEventListener("click", fetchWeatherForSelectedCity);

// Function to fetch city data from JSON file
function fetchData() {
  return fetch("./city_coordinates.json")
    .then((response) => response.json())
    .then((data) => {
      // Store fetched city data
      cityData = data;
      // Populate the city selection dropdown
      populateSelect(cityData);
    });
}

// Function to populate the city selection dropdown
function populateSelect(cityData) {
  cityData.forEach((cityInfo) => {
    const option = document.createElement("option");
    option.value = cityInfo.city;
    option.textContent = cityInfo.city;
    select.appendChild(option);
  });
}

function formatDate(yyyymmdd) {
  // Extract year, month, and day from the input string
  const year = yyyymmdd.substring(0, 4);
  const month = yyyymmdd.substring(4, 6);
  const day = yyyymmdd.substring(6, 8);

  // Create a Date object from the extracted values
  const date = new Date(`${year}-${month}-${day}`);

  // Define options for formatting the date
  const options = {
    weekday: "long", // Full weekday name
    day: "numeric", // Numeric day of the month
    month: "long", // Full month name
    year: "numeric", // Numeric year
  };

  // Format the date using toLocaleDateString
  const formattedDate = date.toLocaleDateString(undefined, options);

  return formattedDate;
}

const weatherMapping = {
  clear: "weather-icon-clear",
  pcloudy: "weather-icon-pcloudy",
  mcloudy: "weather-icon-mcloudy",
  cloudy: "weather-icon-cloudy",
  rain: "weather-icon-rain",
  humid: "weather-icon-humid",
  ishower: "weather-icon-shower",
  lightrain: "weather-icon-lightrain",
  oshower: "weather-icon-shower",
  snow: "weather-icon-snow",
  lightsnow: "weather-icon-snow",
  ts: "weather-icon-thunderstorm",
  rainsnow: "weather-icon-rainsnow",
};

const weatherTypeMapping = {
  clear: "Clear",
  pcloudy: "Partially cloudy",
  mcloudy: "Mostly cloudy",
  cloudy: "Cloudy",
  rain: "Rain",
  humid: "Humid",
  ishower: "Shower",
  lightrain: "Light rain",
  oshower: "Occasional shower",
  snow: "Snow",
  lightsnow: "Light snow",
  ts: "Thunderstorm",
  rainsnow: "Rain and snow",
};

function updateSwiper(data) {
  var swiperWrapper = document.querySelector(".swiper-wrapper");
  swiperWrapper.innerHTML = ""; // Clear existing content

  data.dataseries.forEach((item) => {
    const formattedDate = formatDate(item.date.toString());
    const slide = document.createElement("div");

    slide.className =
      "swiper-slide rounded-edges p-1 mt-15 mb-15 d-flex flex-column justify-content-around";

    // Create a <p> element for the weather text
    const weatherDiv = document.createElement("div");

    // Create a <span> element for the weather icon
    const weatherIcon = document.createElement("span");
    weatherIcon.className = "weather-icon";

    const weatherIconClass = weatherMapping[item.weather];
    if (weatherIconClass) {
      weatherIcon.classList.add(weatherIconClass);
    }

    // Append the weather icon to the weather paragraph
    weatherDiv.appendChild(weatherIcon);

    slide.appendChild(weatherDiv);
    slide.innerHTML += `
      <h4>${weatherTypeMapping[item.weather]}</h4>
      <p>Max: <strong>${item.temp2m.max}</strong></p>
      <p>Min: <strong>${item.temp2m.min}</strong></p>
      <p class="small">${formattedDate}</p>
    `;

    swiperWrapper.appendChild(slide);
  });

  swiper.update(); // Update Swiper after changing content
}

// Function to fetch weather data for a specific city
function getWeather(longitude, latitude, city, country) {
  const url = `https://www.7timer.info/bin/civillight.php?lon=${longitude}&lat=${latitude}&ac=0&unit=metric&output=json&tzshift=0`;

  return fetch(url)
    .then((response) => response.json())
    .then((data) => {
      let html = `<h3>Daily weather for the next 7 day for ${city}, ${country}</h3>`;
      cityName.innerHTML = html;
      updateSwiper(data);
    });
}

// Function to fetch and display weather data for the selected city
function fetchWeatherForSelectedCity() {
  const selectedCity = select.value;
  if (selectedCity) {
    const cityInfo = cityData.find((city) => city.city === selectedCity);
    if (cityInfo) {
      // Call the getWeather function with city details
      getWeather(
        cityInfo.longitude,
        cityInfo.latitude,
        cityInfo.city,
        cityInfo.country
      );
    }
  }
}

// Fetch city data
fetchData();

## Project Scenario

[Coursera Project](https://www.coursera.org/projects/showcase-build-a-website-api-html-javascript-json)

### Technologies Used

- **HTML**: The backbone of the webpage's structure and content.
- **JavaScript**: Used to interact with the 7Timer API and handle data retrieval.
- **CSS & Bootstrap**

### External API

For this project, I integrated the 7Timer API, a free and accessible weather forecast service that does not require API keys.

### Key Methods and Functions

Here are some of the key methods and functions used in the project code:

1. **fetchData()**: This function fetches city data from a JSON file. It uses the `fetch` API to retrieve data and populates the city selection dropdown.

2. **populateSelect(cityData)**: This function populates the city selection dropdown with city names. It is called after fetching city data.

3. **formatDate(yyyymmdd)**: This utility function formats a date in YYYYMMDD format into a more human-readable format, including the full weekday name, numeric day of the month, full month name, and numeric year.

4. **updateSwiper(data)**: This function updates the Swiper component with weather forecast data. It dynamically creates and adds slides to display weather information for the next 7 days.

5. **getWeather(longitude, latitude, city, country)**: This function fetches weather data for a specific city using the 7Timer API. It constructs the API URL based on the city's coordinates and updates the Swiper with the retrieved weather data.

6. **fetchWeatherForSelectedCity()**: This function is called when the user clicks the "Fetch Weather" button. It retrieves the selected city's information from the city data and then calls `getWeather` to fetch and display weather data for that city.

## App Screenshot

![App Screenshot](https://github.com/Gosia-Ras/weather-api-project/blob/e6f0be6a447a94460924a8b4dc79d8624d4fff23/Screenshot%202023-09-29%20124908.png)

## Getting Started

To explore this project and its functionalities, follow these steps:

1. Clone this repository to your local machine.

   ```bash
   git clone https://github.com/Gosia-Ras/weather-api-project.git
   ```

2. Open the `index.html` file in your preferred web browser to access the weather forecast webpage.

3. Start exploring the 7-day weather forecasts for major European cities.

## Feedback and Contributions

Feedback, bug reports, and contributions are highly encouraged and appreciated. If you have suggestions for improvement or would like to contribute to this project, please feel free to open an issue or submit a pull request.

## Authors

- [Gosia Hildebrand](https://github.com/Gosia-Ras/)

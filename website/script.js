const list = document.querySelector("ul#items")

fetch("http://127.0.0.1:8000/descriptive/", {
    method: "GET",
    headers: {
        "Content-Type": "application/json"
    }
})
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok')
        }
        return response.json()
    })
    .then(data => {
        data.forEach(item => {
            list.insertAdjacentHTML("beforeend", `
                <li>
                    <img src="${item["img_link"]}" alt="">
                    <ul>
                        <li> ${item["product"]} </li>
                        <li> ${item["variant"]} </li>
                        <li> ${item["size"]} </li>
                        <li> ${item["url"]} </li>
                        <li> ${item["price"]} </li>
                    </ul>
                </li>
            `)
        })
        // keys are product, variant, size, img_link, url, size, price
        // img_link prefix is https:
        // url prefix is https://us.supreme.com/products
    })
    .catch(error => {
        console.error(`There has been a problem with your fetch operation: ${error}`);
        throw error
    })


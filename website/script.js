const items = document.querySelector("div#items")

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
        console.log(data)

        data.forEach(item => {
            const item_element = document.createElement("div.item")
            item_element.insertAdjacentHTML("beforeend", `
                <span> ${item["product"]}: ${item["price"]}</span>
            `)
            item["variants"].forEach(variant => {
                items.insertAdjacentElement("beforeend", item_element)
                item_element.insertAdjacentHTML("beforeend",
                    `
                        <div class="item">
                            <img src=https:${variant["img_link"]} alt="missing">
                            <div class="sizes"></div>
                        </div>
                    `)
                const recent_item_element = document.querySelector("div#items").lastElementChild
                const sizes_list = recent_item_element.lastElementChild.querySelector("div.sizes")
                variant["sizes"].forEach(size => {
                    sizes_list.insertAdjacentHTML("beforeend",
                        `
                        <span> ${size} </span>
                        `)
                })
            })
        })
        // keys are product, variant, size, img_link, url, size, price
        // img_link prefix is https:
        // url prefix is https://us.supreme.com/products
    })
    .catch(error => {
        console.error(`There has been a problem with your fetch operation: ${error}`);
        throw error
    })


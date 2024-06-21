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
        data.forEach(item => {
            const item_element = document.createElement("div")
            item_element.classList.add("item")
            items.insertAdjacentElement("beforeend", item_element)
            item_element.insertAdjacentHTML("beforeend", `
                <span class="details"> ${item["product"]}: $${item["price"]}</span>
            `)
            const variants = document.createElement("div")
            variants.classList.add("variants")
            item_element.insertAdjacentElement("beforeend", variants)
            item["variants"].forEach(variant => {
                const variant_element = document.createElement("div")
                variant_element.classList.add("variant")
                variants.insertAdjacentElement("beforeend", variant_element)
                variant_element.insertAdjacentHTML("beforeend",
                                                `<img src=https:${variant["img_link"]} alt="missing">`)
                const sizes = document.createElement("div")
                sizes.classList.add("sizes")
                variant_element.insertAdjacentElement("beforeend", sizes)
                variant["sizes"].forEach(size => {
                    sizes.insertAdjacentHTML("beforeend", `<span> ${size} </span>`)
                })
            })
        })
        // img_link prefix is https:
        // url prefix is https://us.supreme.com/products
    })
    .catch(error => {
        console.error(`There has been a problem with your fetch operation: ${error}`);
        throw error
    })


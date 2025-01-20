import requests

url = "http://localhost:5000/process"
data = {
    "product_name": "example product",
    "affiliate_link": "http://example.com"
}

response = requests.post(url, json=data)
print(response.json())

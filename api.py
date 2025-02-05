import aiohttp


async def get_product_info(product_name: str):
    async with aiohttp.ClientSession() as session:
        url = f'https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&fields=product_name,nutriments&limit=100&json=1'
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for product in data.get('products', []):
                    name = product.get('product_name', '')
                    if name.lower() == product_name.lower():
                        calories = product.get('nutriments').get(
                            'energy-kcal_100g', 0
                        )
                        return {
                            'name': product['product_name'],
                            'calories_100g': calories
                        }
                return None
            return None

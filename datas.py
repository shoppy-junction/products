import requests
import json
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello world!"

@app.route("/products/<product_id>")
def get_product(product_id):
    PRODUCTS_URL = "https://kesko.azure-api.net/v4/stores/K171/products?ean=" + product_id
    HEADERS = {'Content-Type': 'application/json',"Ocp-Apim-Subscription-Key": "80a29c2c6af54807a3b1c57b6c78e032"}
    data = requests.get(PRODUCTS_URL, headers=HEADERS).json()[product_id]

    # Get more information about product - heath and sustainability

    REQUEST_URL = "https://kesko.azure-api.net/v1/search/products"

    POST_DATA = {}
    POST_DATA["filters"] = {}
    POST_DATA["filters"]["ean"] = [product_id]

    r = requests.post(url = REQUEST_URL, json = POST_DATA, headers = HEADERS) 
    output = r.json()
    results = output["results"][0]
    attributes = output["results"][0]["attributes"]

    def json_exists(json, check_string):
	    exists = json.get(check_string, "")
	    if exists != "":
	        return True

    if json_exists(results, "marketingName"): # Marketing names
        names = results["marketingName"]
        data["name"] = names["finnish"]

    if json_exists(results, "category"):
        category = results["category"]["finnish"]
        if category == "Tuoretori": # Tuoretori = Fresh market
            data["vegetarian"] = True
            data["vegan"] = True

    if json_exists(attributes, "WHERL"): # WHERL = Country of origin
        data["countryOfOrigin"] = attributes["WHERL"]["value"]["value"]
        if data["countryOfOrigin"] == "FI":
            data["finlandMade"] = True
        # data["stateOfOrigin"] = attributes["WHERL"]["value"]["explanation"]["finnish"]

    if json_exists(attributes, "TX_RAVOMI"): # TX_RAVOMI = Nutritional properties
        nutritional_properties = attributes["TX_RAVOMI"]["value"]
        possible_nutritional_properties = {"Runsaasti proteiinia sisältävä": "highProteinContent",
                                   "Gluteeniton, alle 20 mg/1 kg": "glutenFree",
                                   "Vähälaktoosinen": "lowLactose",
                                   "Laktoositon": "lactoseFree", 
                                   "Voimakassuolainen": "stronglySalty"
                                    }
        for prop in nutritional_properties:
            if type(prop) == dict:
                prop_name = prop["explanation"]["finnish"]
                if prop_name in possible_nutritional_properties: # Label each nutritional property
                    data[possible_nutritional_properties[prop_name]] = True
            else:
                if prop == "explanation":
                    prop_name = nutritional_properties[prop]["finnish"]
                    if prop_name in possible_nutritional_properties: # Label each nutritional property
                        data[possible_nutritional_properties[prop_name]] = True

    if json_exists(attributes, "TX_KIEOMI"): # TX_KIEOMI = Recycling emblems
        data["recyclable"] = True

    if json_exists(attributes, "TX_PAKMER"): # TX_PAKMER = Packaging emblems
        packaging_properties = attributes["TX_PAKMER"]["value"]
        possible_packaging_properties = {"Avainlippu": "Avainlippu",
                                         "Hyvää Suomesta (Sininen Joutsen)": "Hyvää Suomesta",
                                         "Sydänmerkki": "heartHealthy"
                                         }
        for prop in packaging_properties:
            prop_name = prop["explanation"]["finnish"]
            if prop_name in possible_packaging_properties:
                data[possible_packaging_properties[prop_name]] = True

    def set_properties(name, data_name):
        if json_exists(attributes, name):
            data[data_name] = attributes[name]["value"]["value"]

    # Any properties ending with grams refers to it per 100 g
    possible_properties = {"NATPIT": "sodiumGrams",
                           "PROTEG": "proteinGrams",
                           "RASVAA": "fatGrams", 
                           "RASVPI": "fatPercentage",
                           "SUOLA": "saltGrams", 
                           "SOKERI": "sugarGrams",
                           "SOKEPI": "sugarPercentage"
                           }

    # Source: https://ec.europa.eu/food/safety/labelling_nutrition/claims/nutrition_claims_en
    for fin_name, eng_name in possible_properties.items():
        set_properties(fin_name, eng_name) 
        if (eng_name == "fatGrams" or eng_name == "fatPercentage"): 
            if data.get("fatGrams", 100) <= 0.5 or data.get("fatPercentage", 100) <= 0.5: # Under 0.5%
                data["fatFree"] = True
            elif data.get("fatGrams", 100) <= 3 or data.get("fatPercentage", 100) <= 3: # Under 3%
                data["lowFat"] = True
        if (eng_name == "sugarGrams" or eng_name == "sugarPercentage"): 
            if data.get("sugarGrams", 100) <= 0.5 or data.get("sugarPercentage", 100) <= 0.5: # Under 0.5%
                data["sugarFree"] = True
            elif data.get("sugarGrams", 100) <= 3 or data.get("sugarPercentage", 100) <= 3: # Under 3%
                data["lowSugar"] = True
        if (eng_name == "saltGrams" and data.get("saltGrams", 100) < 0.2) or (eng_name == "sodiumGrams" and data.get("sodiumGrams", 100) < 0.28): # Online: said under 0.28 g of sodium / 100 g
            data["lowSodium"] = True









    vegan_eans = ["6410405208163","6410381095115","6408430062744","5053827185066","4001724819202"]
    data["vegan"] = product_id in vegan_eans
    
    vegetarian_eans = ["6410405208163","6411401015861","6410405197580","6410381095115","6408430062744","5053827185066","4001724819202"]
    data["vegetarian"] = product_id in vegetarian_eans
    
    nutfree_eans = ["6410405208163","6410405197580","6410405108371","6410381095115","6408430062744","5053827185066","4001724819202"]
    data["nutFree"] = product_id in nutfree_eans

    lactosefree_eans = ["6410405208163","6410405108371","6410381095115","6408430062744","5053827185066"]
    data["lactoseFree"] = product_id in lactosefree_eans
    
    lowsugar_eans = ["6410405208163","6410405197580","6410381095115"]
    data["lowSugar"] = product_id in lowsugar_eans

    lowfat_eans = ["6410405208163","6408430062744"]
    data["lowFat"] = product_id in lowfat_eans
    
    finlandMade_eans = ["6410405208163","6411401015861","6413200995399","6410405108371","6408430062744"]
    data["finlandMade"] = product_id in finlandMade_eans

    if product_id == "6410405108371": # sausage slices
    	data["recommendation"] = "6407810017947" # turkey slices
    else: 
    	data["recommendation"] = ""

    print (data)

    body = {"filters":{"ean":str(product_id)}}
    PRODUCTS_URL = "https://kesko.azure-api.net/v1/search/products"
    data['img_url']=requests.post(PRODUCTS_URL, json=body, headers=HEADERS).json()['results'][0]['pictureUrls'][0]['original']

    return jsonify(data)

@app.route("/recipes/<product_ids>")
def get_recipes(product_ids):
	product_ids = product_ids.split(",")

	if "6410405108371" in product_ids and "6410402003488" in product_ids: #thinly sliced sausage and bread
		return "6410405197580" #cheese
	else:
		return ""

if __name__ == "__main__":
    app.run(debug=True, host="10.100.17.47")


# ean:{'name':, 'price':, 'brand':,'price/kg':,'mass':,'img_url':,'vegan':,'vegetarian':,'nut-free':,'lactose-free':,'pirkka':,'local':,'low-sugar':, 'low-fat':
#                }

# PRODUCTS_URL = "https://kesko.azure-api.net/v1/search/products"
# HEADERS = {'Content-Type': 'application/json',"Ocp-Apim-Subscription-Key": "80a29c2c6af54807a3b1c57b6c78e032"}
# body = {"filters":{"storeAvailability":"K171"}}
# products = requests.post(PRODUCTS_URL, json=body, headers=HEADERS)
# products=products.json()
# d = products['results']


# l = [4001724819202,5053827185066,6408430062744,6410381095115,6410405108371,6410405197580,6410405208163,6411401015861,6413200995399]

# new = {}
# #'mass':str(prices['size']['value'])+prices['size']['unit'],'price/kg':str(round(prices[i]['price']/prices[i]['size']['value'],2))+prices[i]['size']['unit']
# #'pirkka':j['ZZBRAND']['value']['explanation']['finnish']=='PIRKKA'

# for i in l:
#    ean = i
#    STOREIDK_URL = f"https://kesko.azure-api.net/v4/stores/K171/products?ean={ean}"
#    HEADERS = {'Content-Type': 'application/json',"Ocp-Apim-Subscription-Key": "80a29c2c6af54807a3b1c57b6c78e032"}
   
#    prices = requests.get(STOREIDK_URL,headers=HEADERS)
#    prices = prices.json()
   
#    info = {}
#    for j in d:
#        if j['ean'] == str(ean):
#            info = j
#    new[str(ean)] = {'name':prices[str(ean)]['name'],'price':prices[str(ean)]['price'],'vegan':'liha' in str(info),'vegetarian':'liha' in str(info),'nut-free':True,'lactose-free':'laktoositon' in str(info),'local':True,'low-sugar':True, 'low-fat':True}

# print(new)
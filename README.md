# wikidata-property-finder
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Otamio/wikidata-property-finder/HEAD)

This REPO contains the ISI PropertyFinder using REST endpoints.

PropertyFinder tries to find linkages between dataset columns and wikidata properties. PropertyFinder automatically suggests wikidata properties based on the query string (e.g. column header name) and annotation fields (e.g. role & type).

---
## Backend Setup
To run `PropertyFinder` on a virtual environment:
1. Clone this REPO
2. Create a python virtual environment through conda

`conda create --name propertyfinder python=3.7`

`conda activate propertyfinder`

3. Install dependencies from requirements.txt

`cd wikidata-property-finder`

`pip install -r requirements.txt`

4. Start the program

`python app.py`


To run `PropertyFinder` on Binder:
1. Click the binder link from this repo
2. Execute the notebook `StartonBinder.ipynb`

---
## Example Usage
- Users can find API usages in the notebook `Demo.ipynb`

The most basic request is in the form, which returns wikidata properties most relevant to the input `str`
`http://localhost:12576/search?label=<str>`

Users are also allowed to specify the data_types, scope, and size of properties returned by passing additional parameters. The description of these parameters are specified in the `Inputs` section. The usage of these parameters are:

`http://localhost:12576/search?label=<str>&data_type=<type>&scope=<scope>&size=<size>`

---
## Inputs
Currently, `PropertyFinder` accepts the following parameters:
1. label (string to match): column header name, or user-defined input.

2. data_type: wikidata type of the property,
- quantity
- item / wikibase-item
- time
- id / external-id
- etc.

3. scope:
- `qualifier`
- `main value`
- `both': `qualifier` and `main value`

# wikidata-property-finder

PropertyFinder tries to find linkages between dataset columns and wikidata properties.

PropertyFinder automatically suggests a wikidata property based on the query string (e.g. column header name) and annotation fields (e.g. role & type).

---
Input:
Currently, PropertyFinder accepts the following parameters:
1. label (string to match): column header name, or user-defined input.

2. data_type: wikidata type of the property,
- quantity
- item / wikibase-item
- time
- id / external-id
- etc.

3. scope:
- ‘qualifier’
- ‘main value’
- 'both': 'qualifier' and 'main value'

## OS NGD & Data Hub Source Index

Authoritative links and reference materials used by the MCP server for harvesting,
schema variance checks, and knowledge base enrichment. This consolidates the
public docs so that automated tooling (harvester, future QA generator) can
record provenance and detect drift.

### Core Portals
- OS Data Hub Portal: https://osdatahub.os.uk/
- NGD Overview: https://labs.os.uk/public/os-ngd

### API Base Endpoints (OGC API Features)
- NGD Features (current): https://api.os.uk/features/ngd/ofa/v1/
  - Collections: https://api.os.uk/features/ngd/ofa/v1/collections
  - OpenAPI Spec: https://api.os.uk/features/ngd/ofa/v1/api
  - Example Collection Queryables (pattern): https://api.os.uk/features/ngd/ofa/v1/collections/{collectionId}/queryables
  - Items (features): https://api.os.uk/features/ngd/ofa/v1/collections/{collectionId}/items

### Linked Identifiers API
- Base: https://api.os.uk/search/links/v1/
- Identifier Types pattern: https://api.os.uk/search/links/v1/identifierTypes/{identifierType}/{identifier}

### (Planned / Pending) Additional APIs
> The Places API endpoints are intentionally excluded until access is enabled.

### Markdown Data Structure Pages (selected examples)
- Transport Network: Street https://docs.os.uk/osngd/data-structure/transport/transport-network/street.md
- Transport Network: Road https://docs.os.uk/osngd/data-structure/transport/transport-network/road.md
- Transport Network: Tram on Road https://docs.os.uk/osngd/data-structure/transport/transport-network/tram-on-road.md
- Transport Network: Road Node https://docs.os.uk/osngd/data-structure/transport/transport-network/road-node.md
- Transport Network: Road Link https://docs.os.uk/osngd/data-structure/transport/transport-network/road-link.md
- Transport Network: Road Junction https://docs.os.uk/osngd/data-structure/transport/transport-network/road-junction.md

Add further thematic markdown links (land, buildings, sites, water, greenspace) as they
are integrated into automated variance checks.

### Authentication & Keys
- API Key acquisition: https://osdatahub.os.uk/developer/api-keys

### Licensing & Terms
- Terms of Use: https://osdatahub.os.uk/legal

### Rate Limits & Usage
Publicly documented rate limits are subject to change; current client code
includes a conservative delay (see `OSAPIClient.request_delay`). Adjust after
empirical validation.

### Provenance Recording Plan
Future harvester enhancement will pull each markdown document above and store
content hashes in `data/metadata/docs_snapshot_<ts>.json` enabling:
1. Drift detection (content hash change)
2. Field / enum extraction provenance tagging
3. Reproducible gold-standard question generation referencing doc versions

### Open Tasks
- [ ] Expand markdown link list for buildings, land use, sites, water, greenspace
- [ ] Implement markdown fetch & hash persistence
- [ ] Implement variance report comparing live queryables vs documented fields
- [ ] Tag each generated QA pair with doc hash references

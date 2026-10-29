# The Future Farmer's Table

A concept store for food-tech grow kits and hands-on workshops, designed and built by Hayun Kim for SI 407 (University of Michigan). Products, workshops and prices are fictional; the cart and checkout are a demo and never take payment.

**Problem statement:** How might we help first-time growers with little space quickly find a kit that fits their space, skill level and budget, and feel sure they'll actually harvest something?

## How it's built

- Static HTML, CSS and vanilla JavaScript modules. No framework, no build step on the server.
- Pages are generated from `tools/content.py` by `tools/build.py`:

  ```sh
  python3 tools/build.py
  ```

- `assets/js/` holds the interactions: cart and saved items (`store.js`, kept in `localStorage`), search, the fit finder, shop filters, the harvest timeline, workshop booking, lesson progress and the demo checkout.
- Fonts (Syne, Geist, Geist Mono) are self-hosted under the SIL Open Font License; see `assets/fonts/`.
- Deployed on Vercel with clean URLs (`vercel.json`).

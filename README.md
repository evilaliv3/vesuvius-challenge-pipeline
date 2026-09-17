# vesuvius-challenge-pipeline

Work on the Vesuvius Challenge by Giovanni Pellerano ([`evilaliv3`](https://github.com/evilaliv3)),
on a machine with sixteen cores, no GPU and the published data.

Published work only, one piece per folder under [`results/`](results), frozen. A folder is named
`<uuid4 prefix>-<slug>`: the prefix is assigned once and never reused, so a piece of work can be
named without depending on its title. Inside it, `article.pdf` and the `src/` every
number and figure is rebuilt from. What is still being made is not here, and arrives when it is out.

The data stays out: CT volumes, surface predictions, published segments and model checkpoints
belong to the Vesuvius Challenge and are fetched from its open bucket.

Code MIT, data and figures and written analysis CC BY-NC 4.0: [`LICENSE`](LICENSE).

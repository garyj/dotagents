# Set up the file host

## Run locally

1. Open `services/file-host/` in a terminal.
2. Run `pnpm install --frozen-lockfile`.
3. Generate a local test token without printing it:

   ```bash
   (umask 077; node --input-type=module <<'JS'
   import { randomBytes } from 'node:crypto';
   import { writeFileSync } from 'node:fs';
   writeFileSync('.dev.vars', `FILE_HOST_TOKEN=${randomBytes(32).toString('hex')}\n`, { flag: 'wx', mode: 0o600 });
   JS
   )
   ```

4. Run `pnpm check`.
5. Run `pnpm dev`.
6. In another terminal in the same directory, upload a test file:

   ```bash
   source .dev.vars
   file='/absolute/path/to/test.png'
   printf 'X-Upload-Token: %s\n' "$FILE_HOST_TOKEN" |
       curl --silent --show-error --fail-with-body --globoff \
           --header @- --upload-file "$file" 'http://localhost:8787/'
   ```

7. Open the returned URL in a browser. For a video, verify playback and seeking.

## Configure production

Production changes require the owner's approval under the repository's standing instructions.
Complete local checks and independent review before requesting deployment approval.

1. Run `pnpm exec wrangler whoami` and confirm the account that owns the selected domain.
2. If necessary, run `pnpm exec wrangler login` to select the correct account.
3. Set `CLOUDFLARE_ACCOUNT_ID` in the deployment environment when the login has access to multiple accounts.
4. Create the dedicated bucket with `pnpm exec wrangler r2 bucket create agent-files`.
5. Keep the bucket's public development URL and direct custom-domain access disabled.
6. Generate a separate production upload token in your credential store. Keep the local test token separate.
7. Export only `FILE_HOST_TOKEN` to a `.env` file outside this repository with file permissions `0600`.
8. Deploy the Worker and secret together with `pnpm exec wrangler deploy --secrets-file /secure/path/file-host.env`.
9. In Cloudflare, open the `agent-file-host` Worker.
10. Under **Settings > Domains & Routes > Add > Custom Domain**, attach the chosen hostname after checking it is unused.
11. Set `FILE_HOST_URL` to that HTTPS origin and `FILE_HOST_TOKEN` to the production token in your agents' environment.
12. Use the file-upload skill to publish a harmless test image and recording. Verify the URL, headers, playback, and seeking.

Keep account identifiers, the hostname, and tokens out of tracked files. This Wrangler configuration omits
`routes`, leaving the custom-domain association in Cloudflare. It disables `workers.dev` and preview URLs.
After the initial deployment, `pnpm deploy` inherits the existing secret. To rotate the token, use
`pnpm exec wrangler secret put FILE_HOST_TOKEN` and update your agents' environment.

## Configure GitHub Actions

Do not enable automatic deployments until the owner approves publishing service changes on merges to `master`.

1. Complete the initial production setup above, including the Worker secret and custom domain.
2. Create a Cloudflare API token using the **Edit Cloudflare Workers** template, scoped to the deployment account.
3. In the GitHub repository, open **Settings > Secrets and variables > Actions**.
4. Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as repository secrets.
5. Merge the approved service and [workflow](../../.github/workflows/file-host.yml) into `master`.
6. Open **Actions > Deploy file host** and verify the deployment.

The workflow installs the pinned pnpm version, runs `pnpm check`, and deploys with `pnpm deploy`.
Pushes to `master` trigger it when `services/file-host/**` or the workflow changes. To redeploy manually,
select **Run workflow** on `master`. Other branches cannot deploy through this workflow.

Keep `FILE_HOST_TOKEN` as a Worker runtime secret. GitHub Actions inherits it from the initial deployment.
Service deployments preserve uploaded R2 objects. Artifact uploads do not trigger a deployment.

See [Cloudflare's GitHub Actions guide](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)
for API token setup.

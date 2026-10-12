# Portfolio Lab client preview

This Expo/TypeScript shell targets Android and web. It shows synthetic sample screens for Experiments, New experiment, Experiment detail, and Results. There is no live API yet: Start experiment is disabled, no job ID or measured performance is invented, and iOS is deferred.

Use Node 22.23.2 (`.nvmrc`). From this directory:

```powershell
nvm use 22.23.2
node --version # confirm 22.23.2 before running npm
npm ci
npm run typecheck
npm test
npm run export:web
npm run web
```

The web command starts a local preview. Android JavaScript/Hermes bundle verification uses `npx expo export --platform android`; a physical Android run and TalkBack review are still needed. On this PC, new shells sometimes select an older nvm symlink even after `nvm use`. If `node --version` is below 22.13, put `C:\Users\rlin7\AppData\Local\nvm\v22.23.2` first on that shell's PATH and retry. The project-local `.expo-tmp` and `.jest-cache` directories are ignored build scratch space.

The seven component tests cover the preview flow only. Live submission, job status, cancellation, persistence, and service recovery await the Spring Boot/worker slice. npm's current production-dependency audit reports advisories; resolve and rerun security checks before publication or network exposure.

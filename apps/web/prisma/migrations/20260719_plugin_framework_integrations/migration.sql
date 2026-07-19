-- Phase 9 Sprint 5 — Plugin Framework, Extension SDK & Third-Party Integrations (UP)

CREATE TABLE IF NOT EXISTS "Plugins" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "pluginType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'registered',
  "currentVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "manifestJson" JSONB,
  "signature" TEXT NOT NULL DEFAULT '',
  "publisherKey" TEXT NOT NULL DEFAULT '',
  "minPlatformVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "maxPlatformVersion" TEXT NOT NULL DEFAULT '99.99.99',
  "sandboxReady" BOOLEAN NOT NULL DEFAULT TRUE,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Plugins_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "Plugins_organizationId_idx" ON "Plugins"("organizationId");
CREATE INDEX IF NOT EXISTS "Plugins_ownerUserId_idx" ON "Plugins"("ownerUserId");
CREATE INDEX IF NOT EXISTS "Plugins_pluginType_idx" ON "Plugins"("pluginType");
CREATE INDEX IF NOT EXISTS "Plugins_status_idx" ON "Plugins"("status");
CREATE INDEX IF NOT EXISTS "Plugins_slug_idx" ON "Plugins"("slug");

CREATE TABLE IF NOT EXISTS "PluginVersions" (
  "id" TEXT PRIMARY KEY,
  "pluginId" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "changelog" TEXT NOT NULL DEFAULT '',
  "manifestJson" JSONB,
  "signature" TEXT NOT NULL DEFAULT '',
  "checksum" TEXT NOT NULL DEFAULT '',
  "compatibilityJson" JSONB,
  "createdBy" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PluginVersions_pluginId_version_key" UNIQUE ("pluginId", "version"),
  CONSTRAINT "PluginVersions_pluginId_fkey" FOREIGN KEY ("pluginId")
    REFERENCES "Plugins"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "PluginVersions_pluginId_createdAt_idx"
  ON "PluginVersions"("pluginId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "InstalledPlugins" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "pluginId" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'installed',
  "installedBy" TEXT NOT NULL DEFAULT '',
  "configId" TEXT,
  "installedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "InstalledPlugins_organizationId_pluginId_workspaceId_key"
    UNIQUE ("organizationId", "pluginId", "workspaceId"),
  CONSTRAINT "InstalledPlugins_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "InstalledPlugins_pluginId_fkey" FOREIGN KEY ("pluginId")
    REFERENCES "Plugins"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "InstalledPlugins_organizationId_idx" ON "InstalledPlugins"("organizationId");
CREATE INDEX IF NOT EXISTS "InstalledPlugins_workspaceId_idx" ON "InstalledPlugins"("workspaceId");
CREATE INDEX IF NOT EXISTS "InstalledPlugins_pluginId_idx" ON "InstalledPlugins"("pluginId");
CREATE INDEX IF NOT EXISTS "InstalledPlugins_status_idx" ON "InstalledPlugins"("status");

CREATE TABLE IF NOT EXISTS "PluginPermissions" (
  "id" TEXT PRIMARY KEY,
  "pluginId" TEXT NOT NULL,
  "installedId" TEXT NOT NULL,
  "permissionKey" TEXT NOT NULL,
  "scope" TEXT NOT NULL DEFAULT 'organization',
  "granted" BOOLEAN NOT NULL DEFAULT TRUE,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PluginPermissions_pluginId_fkey" FOREIGN KEY ("pluginId")
    REFERENCES "Plugins"("id") ON DELETE CASCADE,
  CONSTRAINT "PluginPermissions_installedId_fkey" FOREIGN KEY ("installedId")
    REFERENCES "InstalledPlugins"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "PluginPermissions_pluginId_idx" ON "PluginPermissions"("pluginId");
CREATE INDEX IF NOT EXISTS "PluginPermissions_installedId_idx" ON "PluginPermissions"("installedId");
CREATE INDEX IF NOT EXISTS "PluginPermissions_permissionKey_idx" ON "PluginPermissions"("permissionKey");

CREATE TABLE IF NOT EXISTS "PluginConfigurations" (
  "id" TEXT PRIMARY KEY,
  "installedId" TEXT NOT NULL,
  "configJson" JSONB,
  "secretsRef" TEXT NOT NULL DEFAULT '',
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PluginConfigurations_installedId_key" UNIQUE ("installedId"),
  CONSTRAINT "PluginConfigurations_installedId_fkey" FOREIGN KEY ("installedId")
    REFERENCES "InstalledPlugins"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "IntegrationConnections" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "provider" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'connected',
  "displayName" TEXT NOT NULL DEFAULT '',
  "credentialsRef" TEXT NOT NULL DEFAULT '',
  "metadataJson" JSONB,
  "connectedBy" TEXT NOT NULL DEFAULT '',
  "connectedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "IntegrationConnections_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "IntegrationConnections_organizationId_idx" ON "IntegrationConnections"("organizationId");
CREATE INDEX IF NOT EXISTS "IntegrationConnections_workspaceId_idx" ON "IntegrationConnections"("workspaceId");
CREATE INDEX IF NOT EXISTS "IntegrationConnections_provider_idx" ON "IntegrationConnections"("provider");
CREATE INDEX IF NOT EXISTS "IntegrationConnections_status_idx" ON "IntegrationConnections"("status");

CREATE TABLE IF NOT EXISTS "IntegrationLogs" (
  "id" TEXT PRIMARY KEY,
  "connectionId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "message" TEXT NOT NULL DEFAULT '',
  "success" BOOLEAN NOT NULL DEFAULT TRUE,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "IntegrationLogs_connectionId_fkey" FOREIGN KEY ("connectionId")
    REFERENCES "IntegrationConnections"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "IntegrationLogs_connectionId_createdAt_idx"
  ON "IntegrationLogs"("connectionId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "IntegrationLogs_eventType_idx" ON "IntegrationLogs"("eventType");

CREATE TABLE IF NOT EXISTS "PluginEvents" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "pluginId" TEXT,
  "eventType" TEXT NOT NULL,
  "channel" TEXT NOT NULL DEFAULT 'plugin.lifecycle',
  "payloadJson" JSONB,
  "actorUserId" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PluginEvents_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "PluginEvents_pluginId_fkey" FOREIGN KEY ("pluginId")
    REFERENCES "Plugins"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "PluginEvents_organizationId_createdAt_idx"
  ON "PluginEvents"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PluginEvents_pluginId_idx" ON "PluginEvents"("pluginId");
CREATE INDEX IF NOT EXISTS "PluginEvents_channel_idx" ON "PluginEvents"("channel");
CREATE INDEX IF NOT EXISTS "PluginEvents_eventType_idx" ON "PluginEvents"("eventType");

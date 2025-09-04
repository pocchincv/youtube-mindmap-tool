---
id: 013-settings-modal-component
title: Settings Modal and API Configuration Management
epic: youtube-mindmap-tool
status: backlog
priority: medium
complexity: medium
estimated_days: 2
dependencies: [006-react-app-foundation, 012-google-oauth-integration]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [frontend, react, settings, modal, api-config]
---

# Settings Modal and API Configuration Management

## Description
Implement a comprehensive settings modal for API key management (OpenAI, Google, etc.), user preferences, mock data controls, and system configuration options with secure storage and validation.

## Acceptance Criteria
- [ ] Modal overlay with proper focus management and accessibility
- [ ] API key configuration section with secure input fields
- [ ] STT service selection and priority configuration
- [ ] Mock data toggle controls for development/testing
- [ ] User preference settings (theme, default playlist behavior, etc.)
- [ ] Form validation and error handling for API keys
- [ ] Secure storage of API credentials (encrypted)
- [ ] Test/validate API key functionality
- [ ] Import/export settings configuration
- [ ] Reset to defaults functionality
- [ ] Real-time validation feedback for configuration changes
- [ ] Responsive design for different screen sizes

## Technical Requirements

### Settings Modal Component Structure:
```jsx
<SettingsModal isOpen={isSettingsOpen} onClose={closeSettings}>
  <ModalHeader>
    <Title>Settings</Title>
    <CloseButton onClick={closeSettings} />
  </ModalHeader>
  
  <ModalContent>
    <SettingsTabs activeTab={activeTab} onTabChange={setActiveTab}>
      <TabPanel value="api-keys">
        <APIKeysSection />
      </TabPanel>
      <TabPanel value="stt-services">
        <STTServicesSection />
      </TabPanel>
      <TabPanel value="preferences">
        <UserPreferencesSection />
      </TabPanel>
      <TabPanel value="development">
        <DevelopmentSection />
      </TabPanel>
    </SettingsTabs>
  </ModalContent>
  
  <ModalFooter>
    <SaveButton onClick={handleSaveSettings} disabled={!hasChanges} />
    <ResetButton onClick={handleResetToDefaults} />
    <CancelButton onClick={closeSettings} />
  </ModalFooter>
</SettingsModal>
```

### API Keys Configuration:
```jsx
<APIKeysSection>
  <APIKeyInput
    label="OpenAI API Key"
    name="openai_api_key"
    value={settings.openai_api_key}
    onChange={handleAPIKeyChange}
    onTest={testOpenAIKey}
    placeholder="sk-..."
    isValid={validationResults.openai}
    errorMessage={errors.openai}
  />
  
  <APIKeyInput
    label="Google Cloud API Key"
    name="google_api_key"
    value={settings.google_api_key}
    onChange={handleAPIKeyChange}
    onTest={testGoogleKey}
    placeholder="AIza..."
    isValid={validationResults.google}
    errorMessage={errors.google}
  />
  
  <APIKeyInput
    label="YouTube Data API Key"
    name="youtube_api_key"
    value={settings.youtube_api_key}
    onChange={handleAPIKeyChange}
    onTest={testYouTubeKey}
    placeholder="AIza..."
    isValid={validationResults.youtube}
    errorMessage={errors.youtube}
  />
</APIKeysSection>
```

### Settings Management APIs:
```
/**
* User Settings Configuration
* Save and retrieve user configuration settings
* Input Parameters: settings_data (object), user_id (string)
* Return Parameters: SettingsResult with saved configuration
* URL Address: /api/settings/user-config
* Request Method: POST/GET
**/

/**
* API Key Validation
* Test and validate API keys for external services
* Input Parameters: api_key (string), service_type (string)
* Return Parameters: ValidationResult with key status and capabilities
* URL Address: /api/settings/validate-api-key
* Request Method: POST
**/

/**
* Mock Data Control
* Toggle mock data usage for development and testing
* Input Parameters: mock_enabled (boolean), mock_services (array)
* Return Parameters: MockConfigResult with current mock settings
* URL Address: /api/settings/mock-config
* Request Method: POST
**/

/**
* Settings Import/Export
* Import or export user configuration settings
* Input Parameters: config_data (object, for import) or user_id (string, for export)
* Return Parameters: ConfigData object with settings
* URL Address: /api/settings/import-export
* Request Method: POST/GET
**/
```

### User Preferences Configuration:
```typescript
interface UserSettings {
  // API Configuration
  apiKeys: {
    openai: string;
    google: string;
    youtube: string;
  };
  
  // STT Service Preferences
  sttServices: {
    primaryService: 'openai' | 'google' | 'local' | 'breeze';
    fallbackServices: string[];
    localWhisperModel: 'tiny' | 'base' | 'small' | 'medium' | 'large';
  };
  
  // User Interface Preferences
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    defaultSplitRatio: number;
    autoplayOnNodeClick: boolean;
    showTimestamps: boolean;
    mindMapAnimations: boolean;
  };
  
  // Development Settings
  development: {
    useMockData: boolean;
    mockYouTubeAPI: boolean;
    mockSTTServices: boolean;
    debugMode: boolean;
  };
}
```

### API Key Security:
- Client-side encryption before sending to backend
- Server-side encryption for database storage
- No API keys stored in localStorage or sessionStorage
- Secure key retrieval with authentication validation

### Form Validation:
```typescript
const validateAPIKey = async (key: string, service: string) => {
  const patterns = {
    openai: /^sk-[a-zA-Z0-9]{48}$/,
    google: /^AIza[0-9A-Za-z\\-_]{35}$/,
    youtube: /^AIza[0-9A-Za-z\\-_]{35}$/
  };
  
  // Format validation
  if (!patterns[service].test(key)) {
    return { isValid: false, error: 'Invalid key format' };
  }
  
  // Functional validation
  try {
    const result = await testAPIKey(key, service);
    return { isValid: result.success, error: result.error };
  } catch (error) {
    return { isValid: false, error: 'Key validation failed' };
  }
};
```

## Definition of Done
- Settings modal opens and closes with proper focus management
- All API key inputs work with validation and testing functionality
- User preferences are saved and applied correctly across the application
- Mock data controls function properly for development workflow
- Form validation provides clear feedback for invalid configurations
- Settings are securely stored and retrieved
- Import/export functionality works for configuration backup/sharing
- Responsive design works across all screen sizes
- Accessibility features work with keyboard navigation and screen readers
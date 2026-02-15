const enUS = {
  common: {
    appName: 'Sky Drama',
    cancel: 'Cancel',
    confirm: 'Confirm',
    save: 'Save'
  },
  language: {
    label: 'Language',
    zhCN: '中文',
    enUS: 'English',
    jaJP: '日本語'
  },
  app: {
    startup: 'Starting...',
    startupHint: 'Starting up, first launch may take a while...'
  },
  confirm: {
    defaultTitle: 'Confirm Action',
    cancel: 'Cancel',
    confirm: 'Confirm'
  },
  login: {
    welcomeBack: 'Welcome back, Director',
    createStudio: 'Create your first studio',
    emailLabel: 'Email',
    passwordLabel: 'Password',
    rememberMe: 'Remember me',
    login: 'Sign In',
    register: 'Sign Up',
    noAccount: "Don't have an account?",
    hasAccount: 'Already have an account?',
    signUpNow: 'Create one now',
    signInNow: 'Go to sign in',
    openSourceOnGithub: 'Open Source on GitHub',
    fillRequired: 'Please complete all required fields',
    actionFailed: 'Request failed, please check your network or account'
  },
  projects: {
    tabs: {
      projects: 'Workbench',
      styles: 'Style Templates',
      api: 'API Settings',
      password: 'Security'
    },
    archiveTitle: 'Script Archive',
    tour: {
      workbenchTitle: 'Workbench',
      workbenchDesc: 'All your scripts and projects are here. Click to start creating.',
      stylesTitle: 'Style Templates',
      stylesDesc: 'Configure and manage your AI image generation styles.',
      apiTitle: 'API Settings',
      apiDesc: 'Manage API keys and connect model providers.',
      securityTitle: 'Security',
      securityDesc: 'Change password and manage account security.',
      listTitle: 'Project List',
      listDesc: 'Create a new project or open an existing one here.<br>Grid and list views are both supported.'
    },
    workbench: {
      title: 'Scripts',
      subtitle: 'Choose a script to continue...',
      loading: 'Loading scripts...',
      archive: 'View archive',
      delete: 'Delete script',
      newProject: 'New Script',
      tour: {
        createTitle: 'Create a new script',
        createDesc: 'Click here to start a new project.',
        listTitle: 'My scripts',
        listDesc: 'Click a script cover to enter, or use buttons below for archive and delete.'
      },
      messages: {
        createFailed: 'Failed to create',
        deleteConfirmTitle: 'Delete Confirmation',
        deleteConfirmText: 'Delete script "{name}"? This action cannot be undone.',
        deleteFailed: 'Delete failed'
      }
    },
    createModal: {
      title: 'Create New Script',
      namePlaceholder: 'Script title...',
      descriptionPlaceholder: 'Short synopsis (optional)...',
      creating: 'Creating...',
      create: 'Create'
    },
    security: {
      title: 'Security',
      subtitle: 'Manage your credentials and session security.',
      currentPassword: 'Current password',
      newPassword: 'New password',
      updatePassword: 'Update Password',
      logout: 'Sign Out',
      messages: {
        fillRequired: 'Please complete all fields',
        passwordUpdated: 'Password updated',
        updateFailed: 'Update failed',
        logoutConfirmTitle: 'Confirm Action',
        logoutConfirmText: 'Director, are you sure you want to sign out?'
      }
    },
    api: {
      title: 'API Settings',
      subtitle: 'Manage your API keys.',
      newKey: 'New Key',
      editConnection: 'Edit Connection',
      newConnection: 'New Connection',
      platformType: 'Platform',
      connectionName: 'Connection Name',
      baseUrl: 'Base URL',
      apiKey: 'API Key',
      keepEmptyHint: '(leave empty to keep current key)',
      endpointOverrides: 'Endpoint Overrides',
      chat: 'Chat',
      image: 'Image',
      video: 'Video',
      fetchVideo: 'Fetch Video',
      audio: 'Audio',
      activeKeys: 'Active API Keys',
      defaultNode: 'default node',
      testing: 'Testing...',
      test: 'Test',
      empty: 'No active keys yet. Add one to start generating.',
      tour: {
        connectTitle: 'Connect Models',
        connectDesc: 'Click to add a new API key.',
        manageTitle: 'Key Management',
        manageDesc: 'Saved keys are listed here. Test connectivity or remove invalid keys.'
      },
      messages: {
        loadFailed: 'Failed to load key list',
        fillKeyInfo: 'Please complete key information',
        fillKey: 'Please enter API key',
        badBaseUrl: 'Invalid Base URL format (must start with http:// or https://)',
        updated: 'Key updated',
        saved: 'Key securely saved',
        saveFailed: 'Save failed, please check network',
        deleteConfirmTitle: 'Destroy Key',
        deleteConfirmText: 'Destroy this key? This action cannot be undone.',
        deleted: 'Key destroyed',
        deleteFailed: 'Delete failed',
        connectionSuccess: 'Connection success! Available models: {models}...',
        connectionFailed: 'Connection failed: {detail}',
        networkError: 'Network error'
      }
    },
    styles: {
      title: 'Style Templates',
      subtitle: 'Define your visual universe.',
      newStyle: 'New Style',
      clickToUpload: 'Click to upload reference image',
      namePlaceholder: 'Style name...',
      save: 'Save to Library',
      empty: 'No styles yet',
      tour: {
        createTitle: 'Create Style',
        createDesc: 'Upload a reference image to create a new AI style template.',
        libraryTitle: 'Style Library',
        libraryDesc: 'All your styles are shown here for quick management.'
      },
      messages: {
        loadFailed: 'Failed to load style library',
        imageProcessed: 'Image cropped to 1:1 ({size}MB)',
        imageProcessFailed: 'Image processing failed, please retry',
        missingForm: 'Please provide name and reference image',
        saved: 'Style template saved',
        saveFailed: 'Save failed',
        deleteConfirmTitle: 'Delete Template',
        deleteConfirmText: 'Delete this style template? This action cannot be undone.',
        deleted: 'Template removed',
        deleteFailed: 'Delete failed',
        imagePasted: 'Image pasted ({size}MB)',
        pasteFailed: 'Image paste failed'
      }
    },
    episode: {
      createdAt: 'Created',
      archive: 'Story Book',
      createEpisode: 'Create Episode',
      writeTitle: 'Write title here...',
      scrapQuestion: 'Delete?',
      status: {
        draft: 'Draft',
        generating: 'Generating',
        completed: 'Completed',
        failed: 'Failed'
      },
      messages: {
        titleRequired: 'Title cannot be empty',
        created: 'Episode created',
        createFailed: 'Create failed',
        updated: 'Revision saved',
        updateFailed: 'Revision failed',
        deleteFailed: 'Delete failed'
      }
    },
    archive: {
      characters: 'Characters',
      noCharacters: 'No character records',
      scenes: 'Scenes',
      noScenes: 'No scene records'
    }
  },
  workbench: {
    resetLayout: 'Reset Layout',
    status: {
      thinking: 'Thinking...',
      refiningPrompts: 'Refining {count} prompts...',
      refinementComplete: 'Refinement Complete',
      terminatedByUser: 'Terminated by user',
      renderingVideo: 'Rendering and composing video, this may take a few minutes...',
      downloadingVideo: 'Downloading video...'
    },
    logs: {
      generatingVisualPrompts: 'Generating {count} visual prompts...',
      refiningItem: '[{current}/{total}] Refining {category}: {preview}...'
    },
    messages: {
      loadFailed: 'Failed to load workbench',
      saveSuccess: 'Saved',
      saveFailed: 'Save failed',
      configSaved: 'Configuration saved',
      promptGenerationStopped: 'Prompt generation stopped',
      creationDone: 'Creation complete!',
      enterPrompt: 'Please enter a prompt',
      overwriteConfirmTitle: 'Reset confirmation',
      overwriteConfirmText: 'Generated content already exists in this episode. Reset will overwrite and clear all current data (characters, scenes, storyboard). This action cannot be undone.',
      userTerminatedRequest: 'Request terminated by user',
      userTerminatedOperation: 'Operation terminated by user',
      operationCancelled: 'Operation cancelled',
      generateError: 'Generation failed: {error}',
      generateInterrupted: 'Generation interrupted: {error}',
      packagingAssets: 'Packaging assets, please wait...',
      exportingStoryboard: 'Exporting storyboard data, please wait...',
      saved: 'Saved',
      downloadStarted: 'Download started',
      exportAssetsFailed: 'Asset export failed',
      exportStoryboardFailed: 'Storyboard export failed',
      exportVideoFailed: 'Video export failed'
    },
    export: {
      title: 'Export',
      assets: 'Export Assets',
      storyboard: 'Export Storyboard',
      video: 'Export Video',
      assetsFileSuffix: 'assets-pack',
      storyboardFileSuffix: 'storyboard-data',
      keepPageOpen: 'Please keep this page open'
    },
    videoLibrary: {
      title: 'Media Library',
      empty: 'No media yet',
      untitled: 'Untitled'
    },
    previewModule: {
      title: 'Preview',
      ratioLandscape: '16:9 Landscape',
      ratioPortrait: '9:16 Portrait',
      noSignal: 'No signal',
      clipLabel: 'Clip {current} / {total}'
    },
    aiDirector: {
      title: 'AI Director',
      tabs: {
        script: 'Script',
        split: 'Storyboard Split'
      },
      promptPlaceholder: 'Enter your instruction...',
      stop: 'Stop',
      send: 'Send'
    },
    modelConfig: {
      title: 'Generation Settings',
      tabs: {
        script: 'Script',
        image: 'Image',
        video: 'Video',
        style: 'Style'
      },
      selectStyle: 'Select Visual Style',
      noStyle: 'No Style',
      apiConnection: 'API Connection',
      loading: 'Loading...',
      selectConnection: 'Select connection...',
      targetModel: 'Target Model',
      fetching: 'Fetching...',
      autoDefault: 'Auto / Default',
      ready: 'Ready',
      voiceLanguage: 'Dialogue Language',
      voiceLanguagePlaceholder: 'Unspecified',
      voiceLanguages: {
        unspecified: 'Unspecified',
        chinese: 'Chinese',
        english: 'English',
        japanese: 'Japanese',
        korean: 'Korean',
        french: 'French',
        german: 'German',
        spanish: 'Spanish'
      },
      videoPrompt: 'Video Prompt',
      removeBgm: 'Remove background music',
      keepVoice: 'Keep character voice',
      keepSfx: 'Keep sound effects'
    },
    executionConsole: {
      title: 'AI Director Console',
      waiting: 'Waiting for instructions...',
      generating: 'Generating: {title}...',
      blockTitles: {
        meta: 'Project Metadata',
        outline: 'Script Outline',
        characters: 'Character List',
        scenes: 'Scene List',
        storyboard: 'Storyboard Script',
        promptRefinement: 'Prompt Refinement',
        storyboardArray: 'AI Storyboard Output'
      },
      outline: {
        setup: 'Setup',
        confrontation: 'Confrontation',
        resolution: 'Resolution'
      },
      meta: {
        projectTitle: 'Project Title',
        corePremise: 'Core Premise'
      },
      segment: 'Segment {number}',
      running: 'Running',
      failed: 'Failed',
      input: 'Input',
      output: 'Output',
      allTasksCompleted: 'All tasks completed'
    },
    scriptEditor: {
      title: 'Script Workbench',
      tabs: {
        characters: 'Characters',
        scenes: 'Scenes',
        storyboard: 'Storyboard'
      },
      emptyWaiting: 'Waiting for AI generation...',
      manualCreate: 'Create script manually',
      defaults: {
        untitledProject: 'Untitled Project',
        newProjectTitle: 'New Project',
        newScene: 'New Scene',
        neutralMood: 'Neutral',
        newScenePrompt: 'Click here to edit scene description...',
        newShot: 'New Shot',
        wideShot: 'Wide Shot',
        newShotPrompt: 'Click here to edit storyboard frame...',
        noPrompt: 'No prompt'
      },
      prompts: {
        requirementPrefix: 'Requirement:'
      },
      generateTypes: {
        image: 'image',
        video: 'video',
        prompt: 'prompt'
      },
      messages: {
        confirmDelete: 'Are you sure you want to delete?',
        deleted: 'Deleted',
        deleteFailed: 'Delete failed',
        updateFailed: 'Update failed',
        referenceConfirm: 'A reference image is already uploaded. Continue and regenerate with the reference plus style?',
        startGenerating: 'Starting {type} generation...',
        generateSuccess: 'Generated successfully',
        promptRefined: 'Prompt refinement complete',
        generateError: 'Generation error: {error}',
        requestFailed: 'Generation request failed',
        generateFailed: 'Generation failed',
        referenceUploaded: 'Reference image uploaded',
        uploadFailed: 'Upload failed'
      }
    },
    scriptCharacters: {
      reference: 'Ref',
      referenceImage: 'Reference image',
      resetImage: 'Reset',
      generatePortrait: 'Generate portrait',
      addCharacter: 'Add Character'
    },
    scriptScenes: {
      clickToEdit: 'Click to edit',
      sceneNumber: 'Scene {number}',
      noImage: 'No image',
      reference: 'Ref',
      referenceImage: 'Reference image',
      resetImage: 'Reset',
      generateSceneImage: 'Generate scene image',
      addScene: 'Add Scene'
    },
    scriptStoryboard: {
      insertBefore: 'Insert shot before',
      insertAfter: 'Insert shot after',
      dragOrEdit: 'Hold to drag / Click to edit',
      clickToEdit: 'Click to edit',
      previewVideo: 'Preview video',
      noPreview: 'No preview',
      redraw: 'Redraw',
      draw: 'Draw',
      requireImageFirst: 'Generate storyboard image first',
      remakeVideo: 'Remake',
      video: 'Video',
      addShot: 'Add Shot'
    },
    characterModal: {
      defaults: {
        mainRole: 'Lead'
      },
      title: 'Add Character',
      nameLabel: 'Character Name',
      namePlaceholder: 'e.g. Han Li',
      roleLabel: 'Role Tag',
      rolePlaceholder: 'e.g. Lead',
      descriptionLabel: 'Character Description',
      descriptionPlaceholder: 'Appearance, personality traits, costume style...',
      confirmAdd: 'Add'
    },
    timeline: {
      library: 'Media Library',
      clipModeTitle: 'Clip mode (enable and click a video block to split)',
      transitionTitle: 'Transitions (WIP)',
      playbackRateTitle: 'Playback speed',
      mainTrack: 'Main Track',
      audioTrack: 'Audio',
      dragVideoHere: 'Drag videos here',
      dragAudioHere: 'Drag audio here',
      splitVideo: 'Split Video',
      splitPointSeconds: 'Split point (seconds)',
      confirmSplit: 'Confirm Split',
      partLabel: 'Part {number}',
      messages: {
        invalidSplitPoint: 'Invalid split point',
        splitDone: 'Split completed',
        crossTrackNotAllowed: 'Cannot move clips across different track types',
        audioToAudioTrackOnly: 'Audio files can only be dropped onto audio tracks',
        audioAdded: 'Audio added',
        videoToMainTrackOnly: 'Only videos can be dropped onto the main track',
        addedToTrack: 'Added to track'
      }
    },
    videoPreview: {
      title: 'Video Preview',
      noSource: 'No video source'
    },
    bookPreview: {
      promptPlaceholderStoryboard: '[Characters]:\n[Scene]:\n[Storyboard Description]:',
      promptPlaceholderScene: '[Scene]:\n[Scene Description]:',
      shot: 'Shot {id}',
      sceneNamePlaceholder: 'Scene name...',
      shotActionPlaceholder: 'Shot action...',
      clickToEditPrompt: 'Click to edit prompt...',
      regenerateOrRefine: 'Redraw / Refine Prompt',
      generationMode: 'Generation Mode',
      generationModes: {
        single: 'Single-frame Storyboard',
        keyframes: 'Keyframes',
        singleLabel: 'Single-frame Storyboard:',
        singleDesc: 'Generate one image containing all key information as the only reference.',
        keyframesLabel: 'Keyframes:',
        keyframesDesc: 'Generate one image per keyframe and send all of them to the video model when multi-image reference is supported.'
      },
      manualPromptPlaceholder: 'Add extra instructions here, or leave empty to reset directly...',
      resetPrompt: 'Reset prompt',
      generateImage: 'Generate image',
      generateVideo: 'Generate video',
      generating: 'GENERATING... {progress}%',
      noImage: 'No Image',
      visualPrompt: 'Visual Prompt',
      readOnly: 'Read-only',
      editable: 'Editable'
    },
    smartText: {
      unknownCharacter: 'Unknown Character',
      unknownScene: 'Unknown Scene',
      unknown: 'Unknown',
      scene: 'Scene',
      noDetails: 'No details provided.'
    },
    tour: {
      aiDirectorTitle: 'AI Director',
      aiDirectorDesc: 'Start AI-assisted creation here to generate scripts, storyboards, and visuals.',
      modelConfigTitle: 'Model Settings',
      modelConfigDesc: 'Tune AI model parameters to shape your creative style.',
      scriptEditorTitle: 'Script Editor',
      scriptEditorDesc: 'AI-generated scripts appear here, and you can edit and refine them freely.',
      previewTitle: 'Live Preview',
      previewDesc: 'Preview generated video results with real-time playback.',
      timelineTitle: 'Timeline',
      timelineDesc: 'Drag assets and edit clips to finalize your video.'
    }
  },
  tour: {
    next: 'Next',
    prev: 'Back',
    done: 'Done'
  }
}

export default enUS

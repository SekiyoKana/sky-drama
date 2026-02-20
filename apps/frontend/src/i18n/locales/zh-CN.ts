const zhCN = {
  common: {
    appName: 'Sky Drama',
    cancel: '取消',
    confirm: '确认',
    save: '保存'
  },
  language: {
    label: '语言',
    zhCN: '中文',
    enUS: 'English',
    jaJP: '日本語'
  },
  app: {
    startup: '正在启动...',
    startupHint: '正在启动，首次加载可能需要一些时间...'
  },
  confirm: {
    defaultTitle: '确认操作',
    cancel: '取消',
    confirm: '确认'
  },
  login: {
    welcomeBack: '欢迎回来，导演',
    createStudio: '创建你的第一个工作室',
    emailLabel: '邮箱',
    passwordLabel: '密码',
    rememberMe: '记住我',
    login: '登 录',
    register: '注 册',
    noAccount: '还没有账号？',
    hasAccount: '已有账号？',
    signUpNow: '立即注册',
    signInNow: '直接登录',
    openSourceOnGithub: 'Open Source on GitHub',
    fillRequired: '请填写完整信息',
    actionFailed: '操作失败，请检查网络或账号'
  },
  projects: {
    tabs: {
      projects: '工作台',
      styles: '风格模板',
      api: 'API 设置',
      password: '安全中心'
    },
    archiveTitle: '故事档案',
    tour: {
      workbenchTitle: '工作台',
      workbenchDesc: '这里是你的所有故事和项目，点击即可进入创作。',
      stylesTitle: '风格模板',
      stylesDesc: '配置和管理你的 AI 绘图风格。',
      apiTitle: 'API 设置',
      apiDesc: '管理你的 API Key，连接各种大模型服务。',
      securityTitle: '安全中心',
      securityDesc: '修改密码和账户安全设置。',
      listTitle: '项目列表',
      listDesc: '点击这里可以新建项目，或者查看已有的项目。<br>支持网格视图和列表视图切换。'
    },
    workbench: {
      title: '故事',
      subtitle: '选择一个故事以继续...',
      loading: '正在加载故事...',
      archive: '查看设定集',
      delete: '删除故事',
      newProject: '新故事',
      tour: {
        createTitle: '创建新故事',
        createDesc: '点击这里开始一个新的创作项目。',
        listTitle: '我的故事',
        listDesc: '点击故事封面进入创作，或者使用下方的按钮进行归档和删除。'
      },
      messages: {
        createFailed: '创建失败',
        deleteConfirmTitle: '删除确认',
        deleteConfirmText: '确认要删除故事 "{name}" 吗？此操作无法撤销。',
        deleteFailed: '删除失败'
      }
    },
    createModal: {
      title: '创建新故事',
      namePlaceholder: '故事标题...',
      descriptionPlaceholder: '简短的故事梗概 (可选)...',
      creating: '创建中...',
      create: '创建'
    },
    security: {
      title: '安全中心',
      subtitle: '管理您的访问凭证和会话安全。',
      currentPassword: '当前密码',
      newPassword: '新密码',
      updatePassword: '更新密码',
      logout: '退出登录',
      messages: {
        fillRequired: '请填写完整',
        passwordUpdated: '密码修改成功',
        updateFailed: '修改失败',
        logoutConfirmTitle: '确认操作',
        logoutConfirmText: '导演，确认要退出登录吗？'
      }
    },
    api: {
      title: 'API 设置',
      subtitle: '管理您的 APIKEY。',
      newKey: '新建密钥',
      editConnection: '编辑连接',
      newConnection: '新建连接',
      platformType: '平台类型',
      platforms: {
        openai: 'OpenAI 兼容',
        ollama: 'Ollama',
        volcengine: '火山引擎'
      },
      platformHints: {
        openai: '适用于 OpenAI 及多数 OpenAI 兼容服务。',
        ollama: '使用 Ollama 标准 API。支持本机或云服务器地址（示例：http://127.0.0.1:11434/api）。',
        volcengine: '默认接入火山方舟（Ark）大模型服务，使用 OpenAI 兼容调用方式。'
      },
      connectionName: '连接名称',
      baseUrl: '接口地址 (Base URL)',
      apiKey: '密钥 (API Key)',
      optional: '可选',
      apiKeyOptionalPlaceholder: '本地 Ollama 通常可留空',
      keepEmptyHint: '(留空不修改)',
      endpointOverrides: '接口重写 (Endpoint Overrides)',
      chat: '对话 Chat',
      image: '绘图 Image',
      video: '视频 Video',
      fetchVideo: '获取视频 Fetch',
      audio: '音频 Audio',
      activeKeys: '活跃 APIKEY',
      defaultNode: '默认节点',
      testing: '测试中...',
      test: '测试',
      empty: '暂无活跃密钥。请添加一个以开始生成。',
      tour: {
        connectTitle: '连接模型',
        connectDesc: '点击添加新的 API Key。',
        manageTitle: '密钥管理',
        manageDesc: '这里显示已保存的密钥。你可以测试连接状态，或删除无效密钥。'
      },
      messages: {
        loadFailed: '无法加载密钥列表',
        fillKeyInfo: '请填写完整的密钥信息',
        fillKey: '请填写密钥',
        badBaseUrl: 'Base URL 格式不正确 (需以 http:// 或 https:// 开头)',
        updated: '密钥已更新',
        saved: '密钥已安全存储',
        saveFailed: '保存失败，请检查网络',
        deleteConfirmTitle: '销毁密钥',
        deleteConfirmText: '确定将此密钥销毁？此操作不可逆。',
        deleted: '密钥已销毁',
        deleteFailed: '删除失败',
        connectionSuccess: '联通成功！可用模型: {models}...',
        connectionSuccessNoModels: '联通成功！当前服务未返回模型列表，请手动确认模型名。',
        connectionFailed: '连接失败: {detail}',
        networkError: '网络错误'
      }
    },
    styles: {
      title: '风格模板',
      subtitle: '定义你的宇宙视觉美学。',
      newStyle: '新建风格',
      clickToUpload: '点击上传参考图',
      namePlaceholder: '风格名称...',
      save: '保存并入库',
      empty: '暂无风格模板',
      tour: {
        createTitle: '创建风格',
        createDesc: '上传一张参考图，创建一个新的 AI 绘画风格模板。',
        libraryTitle: '风格库',
        libraryDesc: '这里展示了你所有的风格收藏，点击即可管理。'
      },
      messages: {
        loadFailed: '无法加载风格库',
        imageProcessed: '图片已处理为1:1比例 ({size}MB)',
        imageProcessFailed: '图片处理失败，请重试',
        missingForm: '请提供名称和参考图',
        saved: '风格模板已保存',
        saveFailed: '保存失败',
        deleteConfirmTitle: '删除模板',
        deleteConfirmText: '确定删除此风格模板？操作无法撤销。',
        deleted: '模板已移除',
        deleteFailed: '删除失败',
        imagePasted: '已粘贴图片 ({size}MB)',
        pasteFailed: '图片粘贴失败'
      }
    },
    episode: {
      createdAt: '创建于',
      archive: '设定集',
      createEpisode: '创建',
      writeTitle: '在此输入标题...',
      scrapQuestion: '确认删除？',
      entryPicker: {
        title: '选择工作台入口',
        subtitle: '你想以哪种方式进入这个章节？',
        episodeWorkbench: '剧集工作台',
        episodeDesc: '继续分镜、画面和视频创作流程',
        novelWorkbench: '小说工作台',
        novelDesc: '以小说创作模式进行章节写作',
        cancel: '先不进入'
      },
      status: {
        draft: '草稿',
        generating: '生成中',
        completed: '已完成',
        failed: '失败'
      },
      messages: {
        titleRequired: '标题不能为空',
        created: '新行已写入',
        createFailed: '写入失败',
        updated: '修订已保存',
        updateFailed: '修订失败',
        deleteFailed: '无法抹除'
      }
    },
    archive: {
      characters: '角色',
      noCharacters: '暂无角色记录',
      scenes: '场景',
      noScenes: '暂无场景记录'
    }
  },
  novelWorkbench: {
    title: '小说工作台',
    back: '返回项目',
    loading: '正在打开小说工作台...',
    chapterLabel: 'Chapter',
    chapterUntitled: '未命名章节',
    unknownCharacter: '未知角色',
    unknownScene: '未知场景',
    photoWallTitle: '人物与场景照片墙',
    addCharacter: '新建人物',
    addScene: '新建场景',
    noReferences: '暂无角色/场景设定图',
    journalTitle: '章节手稿',
    journalHint: '这里用于写作章节正文、段落草稿与旁白。',
    mentionHint: '输入 ＠ 可快速插入人物/场景引用',
    journalPlaceholder: '在此开始你的小说创作...',
    configTitle: 'AI 写作配置',
    save: '保存小说设置',
    messages: {
      loadFailed: '加载小说工作台失败',
      saved: '小说设置已保存',
      saveFailed: '保存小说设置失败',
      nameRequired: '名称不能为空',
      characterCreated: '人物已创建',
      sceneCreated: '场景已创建',
      briefRequired: '请先输入本章简介',
      selectConnection: '请先选择 API 连接',
      selectModel: '请先选择模型',
      selectImageConnection: '请先选择图片生成源',
      selectImageModel: '请先选择图片生成模型',
      planReady: '章节规划已生成，请确认后写作',
      planFailed: '章节规划生成失败',
      planParseFailed: '规划结果解析失败，请重新规划',
      chapterGenerated: '章节正文已生成',
      chapterGenerateFailed: '章节正文生成失败',
      noSelection: '请先在正文中选中需要处理的文本',
      rewritePendingDecision: '请先确认或撤销当前改写结果',
      rewritePreviewReady: '已生成修改预览，请确认或撤销',
      rewriteDone: '选中文本已更新',
      rewriteFailed: '扩写助手执行失败',
      imageGenerating: '正在生成参考图...',
      imageGenerated: '参考图已生成',
      imageGenerateFailed: '参考图生成失败',
      emptyAiResult: 'AI 未返回有效内容',
      deleteCrossUsageConfirm: '该{target}在剧集工作台仍有引用：\n{usages}\n\n是否继续删除？',
      deleteSaveFailed: '删除后保存失败，请重试'
    },
    types: {
      character: '角色',
      scene: '场景'
    },
    sources: {
      novel: '小说',
      script: '剧集',
      asset: '资产'
    },
    creator: {
      characterTitle: '创建人物',
      sceneTitle: '创建场景',
      nameLabel: '名称',
      namePlaceholder: '请输入名称',
      roleLabel: '人物标签',
      rolePlaceholder: '例如：主角、反派、配角',
      moodLabel: '场景氛围',
      moodPlaceholder: '例如：紧张、温暖、压抑',
      descriptionLabel: '描述',
      descriptionPlaceholder: '写下外观、设定或细节...',
      cancel: '取消',
      confirm: '创建'
    },
    detail: {
      typeLabel: '类型',
      sourceLabel: '来源',
      mentionTagLabel: '引用标签',
      roleLabel: '角色标签',
      moodLabel: '场景氛围',
      descriptionLabel: '描述',
      promptLabel: '图片生成提示词',
      empty: '暂无'
    },
    config: {
      model: '写作模型',
      perspective: '叙事视角',
      tone: '文风',
      length: '章节长度',
      temperature: '创造性',
      imageSource: '图片生成源',
      imageModel: '图片生成模型'
    },
    configTags: {
      text: '文本',
      image: '图片'
    },
    card: {
      detail: '详情',
      generateImage: '生成图'
    },
    perspectives: {
      first: '第一人称',
      third: '第三人称',
      omniscient: '全知视角'
    },
    tones: {
      cinematic: '电影感',
      lyrical: '抒情',
      realistic: '写实'
    },
    lengths: {
      short: '短篇',
      medium: '中篇',
      long: '长篇'
    },
    assistant: {
      title: 'AI生成助手',
      briefLabel: '本章节简介',
      briefPlaceholder: '输入本章核心剧情、冲突或目标，助手将先做雪花规划。',
      wordCountLabel: '目标字数',
      planAction: '生成规划',
      replanAction: '重新规划',
      confirmAction: '确认并写作',
      cancelAction: '取消',
      planning: '规划中...',
      writing: '写作中...',
      oneSentenceLabel: '一句话核心梗概',
      summaryLabel: '章节摘要',
      beatsLabel: '剧情节拍',
      charactersLabel: '登场角色',
      scenesLabel: '登场场景',
      suggestedCharacters: '建议角色：{names}',
      suggestedScenes: '建议场景：{names}'
    },
    rewrite: {
      title: '扩写助手',
      selectedLabel: '选中文本',
      modeLabel: '处理模式',
      modeExpand: '扩写',
      modeRewrite: '改写',
      instructionLabel: '修改建议',
      instructionPlaceholder: '例如：加强心理描写，节奏更慢，保留关键对白。',
      targetWordsLabel: '目标字数（可选）',
      targetWordsHint: '此处填写字数',
      targetWordsPlaceholder: '填写字数（可选）',
      autoHint: '提示：选中文本后右键可立即唤起，或静置 10 秒自动唤起。',
      applyExpand: '执行扩写',
      applyRewrite: '执行改写',
      previewReady: '已生成修改片段',
      undoAction: '撤销',
      confirmAction: '确认',
      processing: '处理中...'
    }
  },
  workbench: {
    resetLayout: '重置布局',
    status: {
      thinking: '思考中...',
      refiningPrompts: '正在优化 {count} 条提示词...',
      refinementComplete: '提示词优化完成',
      terminatedByUser: '用户已终止',
      renderingVideo: '正在渲染并合成视频，这可能需要几分钟...',
      downloadingVideo: '正在下载视频...'
    },
    logs: {
      generatingVisualPrompts: '正在生成 {count} 条视觉提示词...',
      refiningItem: '[{current}/{total}] 正在优化 {category}: {preview}...'
    },
    messages: {
      loadFailed: '加载工作台失败',
      saveSuccess: '保存成功',
      saveFailed: '保存失败',
      configSaved: '配置已保存',
      promptGenerationStopped: '提示词生成已终止',
      creationDone: '创作完成！',
      enterPrompt: '请输入指令',
      overwriteConfirmTitle: '确认重设？',
      overwriteConfirmText: '当前剧集已存在生成内容。重设将覆盖并清空当前所有数据（包括角色、场景和分镜）。此操作不可撤销。',
      userTerminatedRequest: '用户终止了请求',
      userTerminatedOperation: '用户终止了操作',
      operationCancelled: '操作已取消',
      generateError: '生成出错: {error}',
      generateInterrupted: '生成中断: {error}',
      packagingAssets: '正在打包素材，请稍候...',
      exportingStoryboard: '正在导出分镜数据，请稍候...',
      saved: '保存成功',
      downloadStarted: '已开始下载',
      exportAssetsFailed: '素材导出失败',
      exportStoryboardFailed: '导出分镜数据失败',
      exportVideoFailed: '视频导出失败'
    },
    export: {
      title: '导出',
      assets: '导出素材库',
      storyboard: '导出分镜数据',
      video: '导出视频',
      assetsFileSuffix: '素材包',
      storyboardFileSuffix: '分镜数据',
      keepPageOpen: '请勿关闭页面',
      previewTitle: '分镜导出预览',
      previewSubtitle: '共 {count} 个分镜，确认后再导出压缩包',
      promptLoading: '正在加载视频生成请求提示词...',
      noStoryboardData: '当前没有可导出的分镜数据',
      shotLabel: '镜头 {number}',
      promptLabel: '最终视频生成请求提示词',
      styleReferenceLabel: '第一张图片画风参考图',
      videoLinkLabel: '视频链接',
      openVideo: '打开视频',
      noVideoYet: '暂无视频',
      noImage: '暂无图片',
      emptyPrompt: '暂无提示词',
      emptyAction: '未填写镜头动作',
      copyPrompt: '复制提示词',
      copyImage: '复制图片',
      openImage: '打开图片',
      copyAllPrompts: '复制全部提示词',
      closePreview: '关闭',
      confirmExport: '确认导出 ZIP',
      noImageToCopy: '该分镜暂无可复制图片',
      copyPromptSuccess: '已复制分镜提示词',
      copyImageSuccess: '已复制分镜图片',
      copyImageUrlFallback: '当前环境不支持图片复制，已复制图片链接',
      copyAllPromptsSuccess: '已复制全部分镜提示词',
      copyFailed: '复制失败，请重试'
    },
    videoLibrary: {
      title: '素材库',
      empty: '暂无素材',
      untitled: '未命名'
    },
    previewModule: {
      title: '预览窗口',
      ratioLandscape: '16:9 横屏',
      ratioPortrait: '9:16 竖屏',
      noSignal: '暂无信号',
      clipLabel: '片段 {current} / {total}'
    },
    aiDirector: {
      title: 'AI 导演',
      tabs: {
        script: '剧本',
        split: '分镜拆分'
      },
      promptPlaceholder: '输入你的指令...',
      stop: '停止生成',
      send: '发送指令'
    },
    modelConfig: {
      title: '生成设置',
      tabs: {
        script: '剧本',
        image: '画面',
        video: '视频',
        style: '风格'
      },
      selectStyle: '选择视觉风格',
      noStyle: '无风格',
      apiConnection: 'API 连接',
      loading: '加载中...',
      selectConnection: '选择连接...',
      targetModel: '目标模型',
      fetching: '获取中...',
      autoDefault: '自动 / 默认',
      manualModelPlaceholder: '手动输入模型名（例如：llama3.1:8b / ep-xxxx）',
      manualModelHint: '当前服务未返回模型列表，可直接手动填写模型名。',
      ready: '就绪',
      voiceLanguage: '台词语言',
      voiceLanguagePlaceholder: '不指定',
      voiceLanguages: {
        unspecified: '不指定',
        chinese: '汉语',
        english: '英语',
        japanese: '日语',
        korean: '韩语',
        french: '法语',
        german: '德语',
        spanish: '西语'
      },
      videoPrompt: '视频提示',
      removeBgm: '去除背景音乐',
      keepVoice: '保留人物声音',
      keepSfx: '保留人物音效'
    },
    executionConsole: {
      title: 'AI 导演控制台',
      waiting: '等待指令...',
      generating: '生成中: {title}...',
      blockTitles: {
        meta: '项目元数据',
        outline: '剧本大纲',
        characters: '角色列表',
        scenes: '场景列表',
        storyboard: '分镜脚本',
        promptRefinement: '提示词优化',
        storyboardArray: 'AI 分镜生成结果'
      },
      outline: {
        setup: '铺垫',
        confrontation: '冲突',
        resolution: '结局'
      },
      meta: {
        projectTitle: '项目标题',
        corePremise: '核心梗概'
      },
      segment: '片段 {number}',
      running: '运行中',
      failed: '失败',
      input: '输入参数',
      output: '输出结果',
      allTasksCompleted: '全部任务完成'
    },
    scriptEditor: {
      title: '剧本工作台',
      tabs: {
        characters: '角色',
        scenes: '场景',
        storyboard: '分镜'
      },
      emptyWaiting: '等待 AI 生成...',
      manualCreate: '手动创建剧本',
      defaults: {
        untitledProject: '未命名项目',
        newProjectTitle: '新项目',
        newScene: '新场景',
        neutralMood: '中性',
        newScenePrompt: '请点击此处编辑场景描述...',
        newShot: '新分镜',
        wideShot: '全景',
        newShotPrompt: '请点击此处编辑分镜画面...',
        noPrompt: '无提示词'
      },
      prompts: {
        requirementPrefix: '要求:'
      },
      generateTypes: {
        image: '图片',
        video: '视频',
        prompt: '提示词'
      },
      messages: {
        confirmDelete: '确定要删除吗？',
        deleted: '已删除',
        deleteFailed: '删除失败',
        updateFailed: '更新失败',
        referenceConfirm: '已上传参考图，将使用参考图和画风生成新的设定图，是否继续？',
        startGenerating: '开始生成 {type}...',
        generateSuccess: '生成成功',
        promptRefined: '提示词优化完成',
        generateError: '生成出错: {error}',
        requestFailed: '生成请求失败',
        generateFailed: '生成失败',
        referenceUploaded: '参考图已上传',
        referenceUploadedButSaveFailed: '参考图已上传，但保存失败，请重试',
        uploadFailed: '上传失败',
        crossWorkspaceDeleteConfirm: '该{target}在小说工作台仍有引用：\n{usages}\n\n是否继续删除？'
      }
    },
    scriptCharacters: {
      reference: '参考',
      referenceImage: '参考图',
      uploadReferenceTitle: '上传角色参考图',
      clickToSelectReference: '点击选择参考图',
      pasteHint: '支持 Ctrl+V 直接粘贴图片',
      currentReferenceHint: '当前正在显示已上传参考图，点击可替换，或 Ctrl+V 粘贴新图',
      uploadAction: '上传参考图',
      resetImage: '重设',
      generatePortrait: '生成立绘',
      addCharacter: '添加角色'
    },
    scriptScenes: {
      clickToEdit: '点击编辑',
      sceneNumber: '第 {number} 场',
      noImage: '暂无图片',
      reference: '参考',
      referenceImage: '参考图',
      uploadReferenceTitle: '上传场景参考图',
      clickToSelectReference: '点击选择参考图',
      pasteHint: '支持 Ctrl+V 直接粘贴图片',
      currentReferenceHint: '当前正在显示已上传参考图，点击可替换，或 Ctrl+V 粘贴新图',
      uploadAction: '上传参考图',
      resetImage: '重设',
      generateSceneImage: '生成场景图',
      addScene: '添加场景'
    },
    scriptStoryboard: {
      insertBefore: '在此前插入分镜',
      insertAfter: '在此后插入分镜',
      dragOrEdit: '按住拖拽排序 / 点击编辑',
      clickToEdit: '点击编辑',
      previewVideo: '预览视频',
      noPreview: '暂无预览',
      redraw: '重绘',
      draw: '绘图',
      requireImageFirst: '需先生成分镜图',
      remakeVideo: '重制',
      video: '视频',
      addShot: '添加分镜'
    },
    characterModal: {
      defaults: {
        mainRole: '主角'
      },
      title: '添加角色',
      nameLabel: '角色名称',
      namePlaceholder: '例如：韩立',
      roleLabel: '角色标签',
      rolePlaceholder: '例如：主角',
      descriptionLabel: '角色描述',
      descriptionPlaceholder: '外貌描写、性格特征、服装风格...',
      confirmAdd: '确认添加'
    },
    timeline: {
      library: '素材库',
      clipModeTitle: '剪辑模式 (点击开启后，点击视频块进行裁剪)',
      transitionTitle: '转场效果(开发中)',
      playbackRateTitle: '倍速播放',
      mainTrack: '主轨道',
      audioTrack: '音频',
      dragVideoHere: '拖拽视频到这里',
      dragAudioHere: '拖拽音频到这里',
      splitVideo: '裁剪视频',
      splitPointSeconds: '分割点 (秒)',
      confirmSplit: '确认裁剪',
      partLabel: '片段 {number}',
      messages: {
        invalidSplitPoint: '无效的时间点',
        splitDone: '裁剪完成',
        crossTrackNotAllowed: '不能跨不同类型的轨道移动',
        audioToAudioTrackOnly: '音频文件只能拖入音轨',
        audioAdded: '已添加音频',
        videoToMainTrackOnly: '只能将视频拖入主轨道',
        addedToTrack: '已添加到轨道'
      }
    },
    videoPreview: {
      title: '视频预览',
      noSource: '暂无视频源'
    },
    bookPreview: {
      promptPlaceholderStoryboard: '[出场人物]:\n[场景]:\n[分镜描述]:',
      promptPlaceholderScene: '[场景]:\n[场景描述]:',
      shot: '镜头 {id}',
      sceneNamePlaceholder: '场景名称...',
      shotActionPlaceholder: '分镜动作...',
      clickToEditPrompt: '点击编辑提示词...',
      regenerateOrRefine: '重绘 / 优化提示词',
      generationMode: '生成模式',
      generationModes: {
        single: '单图分镜',
        keyframes: '关键帧',
        singleLabel: '单图分镜：',
        singleDesc: '生成一张包含所有关键信息的图片，作为唯一参考。',
        keyframesLabel: '关键帧：',
        keyframesDesc: '每个关键帧生成一张图片，全部返回给视频模型，当视频模型支持多图参考时开启。'
      },
      manualPromptPlaceholder: '在此输入补充描述，或留空直接重设...',
      resetPrompt: '重设提示词',
      generateImage: '生成图片',
      generateVideo: '生成视频',
      generating: '生成中... {progress}%',
      noImage: '暂无图片',
      visualPrompt: '视觉提示词',
      readOnly: '只读',
      editable: '可编辑'
    },
    smartText: {
      unknownCharacter: '未知角色',
      unknownScene: '未知场景',
      unknown: '未知',
      scene: '场景',
      noDetails: '暂无详细信息。'
    },
    tour: {
      aiDirectorTitle: 'AI 导演',
      aiDirectorDesc: '在这里开启 AI 辅助创作，生成剧本、分镜和画面。',
      modelConfigTitle: '模型配置',
      modelConfigDesc: '调整 AI 模型参数，定制你的创作风格。',
      scriptEditorTitle: '剧本编辑',
      scriptEditorDesc: 'AI 生成的剧本会在这里显示，你可以自由修改和完善。',
      previewTitle: '实时预览',
      previewDesc: '查看生成的视频效果，支持实时播放和预览。',
      timelineTitle: '时间轴',
      timelineDesc: '拖拽素材、剪辑视频，完成最后的成片制作。'
    }
  },
  tour: {
    next: '下一步',
    prev: '上一步',
    done: '完成'
  }
}

export default zhCN

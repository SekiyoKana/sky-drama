const jaJP = {
  common: {
    appName: 'Sky Drama',
    cancel: 'キャンセル',
    confirm: '確認',
    save: '保存'
  },
  language: {
    label: '言語',
    zhCN: '中文',
    enUS: 'English',
    jaJP: '日本語'
  },
  app: {
    startup: '起動中...',
    startupHint: '起動中です。初回読み込みには少し時間がかかる場合があります...'
  },
  confirm: {
    defaultTitle: '操作の確認',
    cancel: 'キャンセル',
    confirm: '確認'
  },
  login: {
    welcomeBack: 'おかえりなさい、ディレクター',
    createStudio: '最初のスタジオを作成',
    emailLabel: 'メール',
    passwordLabel: 'パスワード',
    rememberMe: 'ログイン情報を保存',
    login: 'ログイン',
    register: '新規登録',
    noAccount: 'アカウントをお持ちでないですか？',
    hasAccount: 'すでにアカウントをお持ちですか？',
    signUpNow: '今すぐ登録',
    signInNow: 'ログインへ',
    openSourceOnGithub: 'Open Source on GitHub',
    fillRequired: '必要な情報をすべて入力してください',
    actionFailed: '処理に失敗しました。ネットワークまたはアカウントをご確認ください'
  },
  projects: {
    tabs: {
      projects: 'ワークベンチ',
      styles: 'スタイルテンプレート',
      api: 'API 設定',
      password: 'セキュリティ'
    },
    archiveTitle: 'スクリプトアーカイブ',
    tour: {
      workbenchTitle: 'ワークベンチ',
      workbenchDesc: 'ここで全ての脚本とプロジェクトを管理できます。クリックして制作を開始してください。',
      stylesTitle: 'スタイルテンプレート',
      stylesDesc: 'AI 画像生成のスタイルを設定・管理します。',
      apiTitle: 'API 設定',
      apiDesc: 'API キーを管理し、各種モデルサービスへ接続します。',
      securityTitle: 'セキュリティ',
      securityDesc: 'パスワード変更やアカウントの安全設定を行います。',
      listTitle: 'プロジェクト一覧',
      listDesc: 'ここで新規プロジェクト作成や既存プロジェクトの確認ができます。<br>グリッド表示とリスト表示を切り替え可能です。'
    },
    workbench: {
      title: '脚本',
      subtitle: '続行する脚本を選択してください...',
      loading: '脚本を読み込み中...',
      archive: '設定集を見る',
      delete: '脚本を削除',
      newProject: '新規脚本',
      tour: {
        createTitle: '新しい脚本を作成',
        createDesc: 'ここをクリックして新しい制作プロジェクトを開始します。',
        listTitle: 'マイ脚本',
        listDesc: '脚本カバーをクリックして制作に入るか、下のボタンでアーカイブ・削除できます。'
      },
      messages: {
        createFailed: '作成に失敗しました',
        deleteConfirmTitle: '削除確認',
        deleteConfirmText: '脚本「{name}」を削除しますか？この操作は取り消せません。',
        deleteFailed: '削除に失敗しました'
      }
    },
    createModal: {
      title: '新しい脚本を作成',
      namePlaceholder: '脚本タイトル...',
      descriptionPlaceholder: '短いあらすじ（任意）...',
      creating: '作成中...',
      create: '作成'
    },
    security: {
      title: 'セキュリティ',
      subtitle: '認証情報とセッションの安全性を管理します。',
      currentPassword: '現在のパスワード',
      newPassword: '新しいパスワード',
      updatePassword: 'パスワードを更新',
      logout: 'ログアウト',
      messages: {
        fillRequired: 'すべて入力してください',
        passwordUpdated: 'パスワードを更新しました',
        updateFailed: '更新に失敗しました',
        logoutConfirmTitle: '操作の確認',
        logoutConfirmText: 'ディレクター、本当にログアウトしますか？'
      }
    },
    api: {
      title: 'API 設定',
      subtitle: 'API キーを管理します。',
      newKey: '新規キー',
      editConnection: '接続を編集',
      newConnection: '新規接続',
      platformType: 'プラットフォーム',
      platforms: {
        openai: 'OpenAI 互換',
        ollama: 'Ollama',
        volcengine: '火山引擎 (Ark)'
      },
      platformHints: {
        openai: 'OpenAI および多くの OpenAI 互換サービス向け。',
        ollama: 'Ollama 標準 API を使用します。ローカル/クラウドのホスト URL に対応します（例: http://127.0.0.1:11434/api）。',
        volcengine: 'ByteDance 火山方舟 (Ark) モデルへ OpenAI 互換方式で接続します。'
      },
      connectionName: '接続名',
      baseUrl: 'Base URL',
      apiKey: 'API キー',
      optional: '任意',
      apiKeyOptionalPlaceholder: 'ローカル Ollama では通常不要',
      keepEmptyHint: '（空欄なら変更しない）',
      endpointOverrides: 'エンドポイント上書き',
      chat: 'チャット',
      image: '画像',
      video: '動画',
      fetchVideo: '動画取得',
      audio: '音声',
      activeKeys: '有効な API キー',
      defaultNode: 'デフォルトノード',
      testing: 'テスト中...',
      test: 'テスト',
      empty: '有効なキーがありません。追加して生成を開始してください。',
      tour: {
        connectTitle: 'モデル接続',
        connectDesc: '新しい API キーを追加します。',
        manageTitle: 'キー管理',
        manageDesc: '保存済みキーの一覧です。接続テストや不要キーの削除ができます。'
      },
      messages: {
        loadFailed: 'キー一覧の読み込みに失敗しました',
        fillKeyInfo: 'キー情報を入力してください',
        fillKey: 'API キーを入力してください',
        badBaseUrl: 'Base URL の形式が正しくありません（http:// または https:// で開始）',
        updated: 'キーを更新しました',
        saved: 'キーを安全に保存しました',
        saveFailed: '保存に失敗しました。ネットワークを確認してください',
        deleteConfirmTitle: 'キー削除',
        deleteConfirmText: 'このキーを削除しますか？この操作は元に戻せません。',
        deleted: 'キーを削除しました',
        deleteFailed: '削除に失敗しました',
        connectionSuccess: '接続成功！利用可能モデル: {models}...',
        connectionSuccessNoModels: '接続成功。モデル一覧は返されませんでした。モデル名を手動で確認してください。',
        connectionFailed: '接続失敗: {detail}',
        networkError: 'ネットワークエラー'
      }
    },
    styles: {
      title: 'スタイルテンプレート',
      subtitle: 'あなたのビジュアル宇宙を定義しましょう。',
      newStyle: '新規スタイル',
      clickToUpload: 'クリックして参照画像をアップロード',
      namePlaceholder: 'スタイル名...',
      save: '保存してライブラリへ',
      empty: 'スタイルはまだありません',
      tour: {
        createTitle: 'スタイル作成',
        createDesc: '参照画像をアップロードして、新しい AI 描画スタイルを作成します。',
        libraryTitle: 'スタイルライブラリ',
        libraryDesc: 'すべてのスタイルをここで確認・管理できます。'
      },
      messages: {
        loadFailed: 'スタイルライブラリの読み込みに失敗しました',
        imageProcessed: '画像を1:1に処理しました ({size}MB)',
        imageProcessFailed: '画像処理に失敗しました。再試行してください',
        missingForm: '名前と参照画像を入力してください',
        saved: 'スタイルテンプレートを保存しました',
        saveFailed: '保存に失敗しました',
        deleteConfirmTitle: 'テンプレート削除',
        deleteConfirmText: 'このスタイルテンプレートを削除しますか？この操作は取り消せません。',
        deleted: 'テンプレートを削除しました',
        deleteFailed: '削除に失敗しました',
        imagePasted: '画像を貼り付けました ({size}MB)',
        pasteFailed: '画像の貼り付けに失敗しました'
      }
    },
    episode: {
      createdAt: '作成日',
      archive: '設定集',
      createEpisode: 'エピソード作成',
      writeTitle: 'ここにタイトルを入力...',
      scrapQuestion: '削除しますか？',
      status: {
        draft: '下書き',
        generating: '生成中',
        completed: '完了',
        failed: '失敗'
      },
      messages: {
        titleRequired: 'タイトルは必須です',
        created: 'エピソードを作成しました',
        createFailed: '作成に失敗しました',
        updated: '修正を保存しました',
        updateFailed: '修正保存に失敗しました',
        deleteFailed: '削除できませんでした'
      }
    },
    archive: {
      characters: 'キャラクター',
      noCharacters: 'キャラクター記録はありません',
      scenes: 'シーン',
      noScenes: 'シーン記録はありません'
    }
  },
  workbench: {
    resetLayout: 'レイアウトをリセット',
    status: {
      thinking: '思考中...',
      refiningPrompts: '{count}件のプロンプトを最適化中...',
      refinementComplete: 'プロンプト最適化完了',
      terminatedByUser: 'ユーザーが中断しました',
      renderingVideo: '動画をレンダリング・合成中です。数分かかる場合があります...',
      downloadingVideo: '動画をダウンロード中...'
    },
    logs: {
      generatingVisualPrompts: '{count}件のビジュアルプロンプトを生成中...',
      refiningItem: '[{current}/{total}] {category} を最適化中: {preview}...'
    },
    messages: {
      loadFailed: 'ワークベンチの読み込みに失敗しました',
      saveSuccess: '保存しました',
      saveFailed: '保存に失敗しました',
      configSaved: '設定を保存しました',
      promptGenerationStopped: 'プロンプト生成を停止しました',
      creationDone: '制作が完了しました！',
      enterPrompt: '指示を入力してください',
      overwriteConfirmTitle: 'リセット確認',
      overwriteConfirmText: 'このエピソードには既に生成済みデータがあります。リセットすると現在の全データ（キャラクター、シーン、分鏡）が上書き・削除されます。この操作は取り消せません。',
      userTerminatedRequest: 'ユーザーがリクエストを中断しました',
      userTerminatedOperation: 'ユーザーが操作を中断しました',
      operationCancelled: '操作をキャンセルしました',
      generateError: '生成エラー: {error}',
      generateInterrupted: '生成中断: {error}',
      packagingAssets: '素材をパッケージ中です。しばらくお待ちください...',
      exportingStoryboard: '分鏡データをエクスポート中です。しばらくお待ちください...',
      saved: '保存しました',
      downloadStarted: 'ダウンロードを開始しました',
      exportAssetsFailed: '素材のエクスポートに失敗しました',
      exportStoryboardFailed: '分鏡データのエクスポートに失敗しました',
      exportVideoFailed: '動画のエクスポートに失敗しました'
    },
    export: {
      title: 'エクスポート',
      assets: '素材をエクスポート',
      storyboard: '分鏡データをエクスポート',
      video: '動画をエクスポート',
      assetsFileSuffix: '素材パック',
      storyboardFileSuffix: '分鏡データ',
      keepPageOpen: 'このページを閉じないでください',
      previewTitle: '分鏡エクスポートプレビュー',
      previewSubtitle: '全 {count} ショット。内容確認後に ZIP を出力します。',
      promptLoading: '動画生成リクエストプロンプトを読み込み中...',
      noStoryboardData: 'エクスポート可能な分鏡データがありません',
      shotLabel: 'ショット {number}',
      promptLabel: '最終動画生成リクエストプロンプト',
      styleReferenceLabel: '1枚目画像の画風参照',
      videoLinkLabel: '動画リンク',
      openVideo: '動画を開く',
      noVideoYet: '動画未生成',
      noImage: '画像なし',
      emptyPrompt: 'プロンプトなし',
      emptyAction: 'ショット動作が未設定です',
      copyPrompt: 'プロンプトをコピー',
      copyImage: '画像をコピー',
      openImage: '画像を開く',
      copyAllPrompts: '全プロンプトをコピー',
      closePreview: '閉じる',
      confirmExport: 'ZIP をエクスポート',
      noImageToCopy: 'このショットにはコピー可能な画像がありません',
      copyPromptSuccess: 'プロンプトをコピーしました',
      copyImageSuccess: '画像をコピーしました',
      copyImageUrlFallback: 'この環境では画像コピーに未対応のため、画像 URL をコピーしました',
      copyAllPromptsSuccess: '全プロンプトをコピーしました',
      copyFailed: 'コピーに失敗しました。再試行してください'
    },
    videoLibrary: {
      title: '素材ライブラリ',
      empty: '素材がありません',
      untitled: '無題'
    },
    previewModule: {
      title: 'プレビュー',
      ratioLandscape: '16:9 横向き',
      ratioPortrait: '9:16 縦向き',
      noSignal: '信号なし',
      clipLabel: 'クリップ {current} / {total}'
    },
    aiDirector: {
      title: 'AI ディレクター',
      tabs: {
        script: '脚本',
        split: '分鏡分割'
      },
      promptPlaceholder: '指示を入力...',
      stop: '停止',
      send: '送信'
    },
    modelConfig: {
      title: '生成設定',
      tabs: {
        script: '脚本',
        image: '画面',
        video: '動画',
        style: 'スタイル'
      },
      selectStyle: 'ビジュアルスタイルを選択',
      noStyle: 'スタイルなし',
      apiConnection: 'API 接続',
      loading: '読み込み中...',
      selectConnection: '接続を選択...',
      targetModel: '対象モデル',
      fetching: '取得中...',
      autoDefault: '自動 / デフォルト',
      manualModelPlaceholder: 'モデル名を手動入力（例: llama3.1:8b / ep-xxxx）',
      manualModelHint: 'このプロバイダーはモデル一覧を返しません。モデル名を直接入力できます。',
      ready: '準備完了',
      voiceLanguage: 'セリフ言語',
      voiceLanguagePlaceholder: '指定なし',
      voiceLanguages: {
        unspecified: '指定なし',
        chinese: '中国語',
        english: '英語',
        japanese: '日本語',
        korean: '韓国語',
        french: 'フランス語',
        german: 'ドイツ語',
        spanish: 'スペイン語'
      },
      videoPrompt: '動画プロンプト',
      removeBgm: 'BGM を除去',
      keepVoice: '人物音声を保持',
      keepSfx: '効果音を保持'
    },
    executionConsole: {
      title: 'AI ディレクターコンソール',
      waiting: '指示を待機中...',
      generating: '生成中: {title}...',
      blockTitles: {
        meta: 'プロジェクトメタデータ',
        outline: '脚本アウトライン',
        characters: 'キャラクター一覧',
        scenes: 'シーン一覧',
        storyboard: '分鏡スクリプト',
        promptRefinement: 'プロンプト最適化',
        storyboardArray: 'AI 分鏡生成結果'
      },
      outline: {
        setup: '導入',
        confrontation: '対立',
        resolution: '結末'
      },
      meta: {
        projectTitle: 'プロジェクトタイトル',
        corePremise: 'コア概要'
      },
      segment: 'セグメント {number}',
      running: '実行中',
      failed: '失敗',
      input: '入力パラメータ',
      output: '出力結果',
      allTasksCompleted: 'すべてのタスクが完了しました'
    },
    scriptEditor: {
      title: '脚本ワークベンチ',
      tabs: {
        characters: 'キャラクター',
        scenes: 'シーン',
        storyboard: '分鏡'
      },
      emptyWaiting: 'AI 生成待機中...',
      manualCreate: '手動で脚本を作成',
      defaults: {
        untitledProject: '無題プロジェクト',
        newProjectTitle: '新規プロジェクト',
        newScene: '新規シーン',
        neutralMood: '中立',
        newScenePrompt: 'ここをクリックしてシーン説明を編集...',
        newShot: '新規ショット',
        wideShot: 'ワイドショット',
        newShotPrompt: 'ここをクリックして分鏡画面を編集...',
        noPrompt: 'プロンプトなし'
      },
      prompts: {
        requirementPrefix: '要件:'
      },
      generateTypes: {
        image: '画像',
        video: '動画',
        prompt: 'プロンプト'
      },
      messages: {
        confirmDelete: '削除してもよろしいですか？',
        deleted: '削除しました',
        deleteFailed: '削除に失敗しました',
        updateFailed: '更新に失敗しました',
        referenceConfirm: '参照画像がアップロード済みです。参照画像と画風を使って再生成しますか？',
        startGenerating: '{type} を生成開始...',
        generateSuccess: '生成成功',
        promptRefined: 'プロンプト最適化完了',
        generateError: '生成エラー: {error}',
        requestFailed: '生成リクエストに失敗しました',
        generateFailed: '生成に失敗しました',
        referenceUploaded: '参照画像をアップロードしました',
        referenceUploadedButSaveFailed: '参照画像はアップロード済みですが、保存に失敗しました。再試行してください。',
        uploadFailed: 'アップロードに失敗しました'
      }
    },
    scriptCharacters: {
      reference: '参照',
      referenceImage: '参照画像',
      uploadReferenceTitle: 'キャラクター参照画像をアップロード',
      clickToSelectReference: 'クリックして参照画像を選択',
      pasteHint: 'Ctrl+V で画像を直接貼り付けできます',
      currentReferenceHint: 'アップロード済み参照画像を表示中です。クリックで差し替え、または Ctrl+V で新しい画像を貼り付けできます。',
      uploadAction: '参照画像をアップロード',
      resetImage: 'リセット',
      generatePortrait: '立ち絵を生成',
      addCharacter: 'キャラクター追加'
    },
    scriptScenes: {
      clickToEdit: 'クリックして編集',
      sceneNumber: '第 {number} シーン',
      noImage: '画像なし',
      reference: '参照',
      referenceImage: '参照画像',
      uploadReferenceTitle: 'シーン参照画像をアップロード',
      clickToSelectReference: 'クリックして参照画像を選択',
      pasteHint: 'Ctrl+V で画像を直接貼り付けできます',
      currentReferenceHint: 'アップロード済み参照画像を表示中です。クリックで差し替え、または Ctrl+V で新しい画像を貼り付けできます。',
      uploadAction: '参照画像をアップロード',
      resetImage: 'リセット',
      generateSceneImage: 'シーン画像を生成',
      addScene: 'シーン追加'
    },
    scriptStoryboard: {
      insertBefore: '前に分鏡を挿入',
      insertAfter: '後ろに分鏡を挿入',
      dragOrEdit: '長押しで並び替え / クリックで編集',
      clickToEdit: 'クリックして編集',
      previewVideo: '動画をプレビュー',
      noPreview: 'プレビューなし',
      redraw: '再描画',
      draw: '描画',
      requireImageFirst: '先に分鏡画像を生成してください',
      remakeVideo: '再作成',
      video: '動画',
      addShot: '分鏡追加'
    },
    characterModal: {
      defaults: {
        mainRole: '主人公'
      },
      title: 'キャラクター追加',
      nameLabel: 'キャラクター名',
      namePlaceholder: '例：韓立',
      roleLabel: '役割タグ',
      rolePlaceholder: '例：主人公',
      descriptionLabel: 'キャラクター説明',
      descriptionPlaceholder: '外見描写、性格、衣装スタイル...',
      confirmAdd: '追加する'
    },
    timeline: {
      library: '素材ライブラリ',
      clipModeTitle: '編集モード（有効化後、動画ブロックをクリックして分割）',
      transitionTitle: 'トランジション（開発中）',
      playbackRateTitle: '再生速度',
      mainTrack: 'メイントラック',
      audioTrack: '音声',
      dragVideoHere: 'ここに動画をドラッグ',
      dragAudioHere: 'ここに音声をドラッグ',
      splitVideo: '動画を分割',
      splitPointSeconds: '分割点（秒）',
      confirmSplit: '分割を確定',
      partLabel: 'パート {number}',
      messages: {
        invalidSplitPoint: '無効な分割位置です',
        splitDone: '分割完了',
        crossTrackNotAllowed: '異なる種類のトラック間では移動できません',
        audioToAudioTrackOnly: '音声ファイルは音声トラックにのみドラッグできます',
        audioAdded: '音声を追加しました',
        videoToMainTrackOnly: '動画はメイントラックにのみドラッグできます',
        addedToTrack: 'トラックに追加しました'
      }
    },
    videoPreview: {
      title: '動画プレビュー',
      noSource: '動画ソースなし'
    },
    bookPreview: {
      promptPlaceholderStoryboard: '[登場人物]:\n[シーン]:\n[分鏡説明]:',
      promptPlaceholderScene: '[シーン]:\n[シーン説明]:',
      shot: 'ショット {id}',
      sceneNamePlaceholder: 'シーン名...',
      shotActionPlaceholder: 'ショット動作...',
      clickToEditPrompt: 'クリックしてプロンプトを編集...',
      regenerateOrRefine: '再描画 / プロンプト最適化',
      generationMode: '生成モード',
      generationModes: {
        single: '単一画像分鏡',
        keyframes: 'キーフレーム',
        singleLabel: '単一画像分鏡：',
        singleDesc: 'すべての重要情報を含む1枚の画像を生成し、唯一の参照として使用します。',
        keyframesLabel: 'キーフレーム：',
        keyframesDesc: '各キーフレームごとに画像を生成し、複数画像参照に対応する動画モデルへまとめて渡します。'
      },
      manualPromptPlaceholder: '補足説明を入力するか、空欄のまま直接リセット...',
      resetPrompt: 'プロンプトをリセット',
      generateImage: '画像を生成',
      generateVideo: '動画を生成',
      generating: '生成中... {progress}%',
      noImage: '画像なし',
      visualPrompt: 'ビジュアルプロンプト',
      readOnly: '読み取り専用',
      editable: '編集可能'
    },
    smartText: {
      unknownCharacter: '不明なキャラクター',
      unknownScene: '不明なシーン',
      unknown: '不明',
      scene: 'シーン',
      noDetails: '詳細情報がありません。'
    },
    tour: {
      aiDirectorTitle: 'AI ディレクター',
      aiDirectorDesc: 'ここから AI 支援制作を開始し、脚本・分鏡・画面を生成します。',
      modelConfigTitle: 'モデル設定',
      modelConfigDesc: 'AI モデルのパラメータを調整し、制作スタイルをカスタマイズします。',
      scriptEditorTitle: '脚本編集',
      scriptEditorDesc: 'AI が生成した脚本がここに表示され、自由に編集・改善できます。',
      previewTitle: 'リアルタイムプレビュー',
      previewDesc: '生成された動画をリアルタイムで再生・確認できます。',
      timelineTitle: 'タイムライン',
      timelineDesc: '素材をドラッグして編集し、最終映像を完成させます。'
    }
  },
  tour: {
    next: '次へ',
    prev: '戻る',
    done: '完了'
  }
}

export default jaJP

// Error handler
const crashWithError = (e) => {
  console.error(e);
  document.getElementById("jatos-error-message").style.display = "";
  document.getElementById("jatos-error-details").innerText = e.toString();
  window.onbeforeunload = null; // Disable the warning on unload
}
window.onerror = (message, source, lineno, colno, error) => crashWithError(error || new Error(message));
window.addEventListener("error", (ErrorEvent) => crashWithError(ErrorEvent.error || new Error(ErrorEvent.message)));
window.addEventListener("unhandledrejection", (event) => crashWithError(event.reason || new Error("Unhandled promise rejection")));


/*
*** CONTENT DEFINITIONS FOR THE EXPERIMENT ***
*/
const stimuliAB = {
  A: [
    { stimulusId: "phrases2b20" },

    { stimulusId: "Haircut16-44p1-2", anchorPosition: "first" },
    { stimulusId: "Haircut16-44p1", anchorPosition: "last" }
  ],
  B: [
    { stimulusId: "phrases2b20" },

    { stimulusId: "Haircut16-44p1-2", anchorPosition: "last" },
    { stimulusId: "Haircut16-44p1", anchorPosition: "first" }
  ],
};
const staticBase = `/static/`;
const soundBaseUrl = `${staticBase}sounds/`;
Object.values(stimuliAB).forEach(g => {
  g.forEach(s => {
    s.wavUrl = `${soundBaseUrl}${s.stimulusId}.wav`
  });
});

const triggerCategories = [
  "Category A",
  "Category B",
  "Category C",
  "Category D",
];

const soundPlayingMp4 = `${staticBase}sound-playing.mp4`;
const soundPlayingGif = `${staticBase}sound-playing.gif`;
const privacyPolicyLink = `privacy.html`;


const welcomeConsentHtml = `
  <h1>Misophonia Study</h1>
  <p>Misophonia is a condition where specific everyday sounds, such as chewing and pen clicking, provoke strong discomfort.</p>
  <p>We are creating a dataset of sound mixes that can be used to develop noise-cancelling headphones that selectively filter out misophonia trigger sounds.</p>
  <p>By participating in this study and rating short audio clips, you will help validate this dataset so it can be openly released for anyone to build on.</p>

  <h2>Instructions</h2>
  <p>You start by answering a brief questionnaire and selecting which types of sounds trigger you. Then, we confirm that you are wearing headphones, or are listening through speakers in a quiet environment.</p>
  <p>You will then listen to and rate some sounds mixtures that may contain trigger sounds. You can skip any sound that is too uncomfortable.</p>

  <h2>Consent</h2>
  <p>
    Your participation is voluntary, and you may skip sounds or withdraw at any time, without any consequences.
  </p>
  <p>
    Please read our <a href="${privacyPolicyLink}" target="_blank">Privacy Policy</a> describing how your data will be handled. Note that the data collected will be anonymized and made publicly available for anyone to use.
  </p>

`;
const consentCheckText = `I am 18 years or older, I have read and understood the information provided, and I consent to participate voluntarily in this study.`;

const stimuliPresentationInstructionsHtml = `
  <h1>Get ready to listen</h1>
  <p>You will now hear a series of sound clips. Please listen to each carefully. Some sounds might be triggering, but you always have the option to skip if they are too uncomfortable.</p>
  <p>After each sound, you will be asked to rate the level of discomfort or anxiety you experienced while listening to it. You will also be asked to select which sound or sounds you think you heard.</p>
`;

const copyrightCredits = `
  Sound playing animation by <a href="https://iconscout.com/free-lottie-animation/free-headphone-animated-icon_13336964" target="_blank">
  Madness Stock on IconScout</a>.
`;

const contactInfo = `
  Contact <a href="mailto:lukt@itu.dk">lukt@itu.dk</a> for any questions or concerns regarding this study. Also refer to our <a href="${privacyPolicyLink}" target="_blank">Privacy Policy</a>.
`;



/*
*** ENSURE ONLY ONE RUN PER BROWSER; AND ONLY ONE BROWSER PER RUN ***
*/
const getShareLink = () => {
  const code = window.jatos.studyCode;
  const origin = window.location.origin;
  return `${origin}/publix/${code}`;
};

const setCookie = (name, value, days) => {
  const d = new Date();
  d.setTime(d.getTime() + (days*24*60*60*1000));
  const expires = "expires="+ d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/";
};
const getCookie = (name) => {
  const cname = name + "=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for(let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(cname) == 0) {
      return c.substring(cname.length, c.length);
    }
  }
  return null;
};


let hasEnsuredOneBrowserPerStudy = false;
const ensureOneBrowserPerStudy = (sharePathname) => {
  // This is essentially a way to change how JATOS behaves
  // We want users to share the link they see in their browser with others, but the ones they share should get a new session
  // And we want to ensure that each browser instance only participates once

  if (hasEnsuredOneBrowserPerStudy) return;
  hasEnsuredOneBrowserPerStudy = true;

  const existingShareParam = (new URL(window.location.href)).searchParams.get("share");

  // Current URL with query parameter share=shareLink (URL encoded)
  const url = new URL(window.location.href);
  url.searchParams.set("share", sharePathname);
  window.history.replaceState({}, document.title, url.toString());

  const cookieName = `${sharePathname}-instance`
  const existing = getCookie(cookieName);
  if (existing) {
    if (existing !== window.location.pathname) {
      // Redirect to the existing cookie URL
      window.onbeforeunload = null;
      window.location.href = existing;
      return;
    }
  }
  else {
    if (existingShareParam) {
      // Already have a share param, so it must come from another browser instance
      window.onbeforeunload = null;
      window.location.pathname = decodeURIComponent(existingShareParam);
      return;
    }
    else {
      // No share param, so must be new
      setCookie(cookieName, window.location.pathname, 90);
    }
  }
};



if ((new URL(window.location.href)).searchParams.has("share")) {
  // if url has resetSession=true, clear the cookie for this share link
  if ((new URL(window.location.href)).searchParams.has("resetSession")) {
    const sharePathname = (new URL(window.location.href)).searchParams.get("share");
    const cookieName = `${sharePathname}-instance`;
    setCookie(cookieName, "", -1); // delete cookie
  }
  ensureOneBrowserPerStudy((new URL(window.location.href)).searchParams.get("share"));
}

// console.log(`Share link for this study: ${getShareLink()}`);



/*
*** HELPER FUNCTIONS USED FOR DEFINING THE EXPERIMENT TIMELINE ***
*/
/* === Study state management === */
const getStudyState = async (key, defaultValue) => {
  const state = window.jatos.studySessionData || {};
  if (!(key in state)) {
    return defaultValue;
  }
  return state[key];
};

const setStudyState = async (key, callback) => {
  const state = window.jatos.studySessionData || {};
  state[key] = callback(state[key]);
  await window.jatos.setStudySessionData(state);
}

const appendResultJson = async (obj) => {
  // Copy object
  const objWithIDs = Object.assign({}, obj);
  const ids  = {};
  window.jatos.addJatosIds(ids);
  objWithIDs.jatosIds = ids;
  const jsonData = JSON.stringify(objWithIDs);
  await window.jatos.appendResultData(jsonData + "\n"); // Make data as JSONL
  console.log(`Appended result data:`, jsonData);
}

const onDataUpdate = async (data) => {
  // Save trial data unless marked otherwise (for analysis)
  if (!data.doNotSave) {
    try {
      await appendResultJson(data);
    } catch (e) {
      crashWithError(Error("Failed to append result data:", e));
    }
  }

  // Save progress for page reloading
  await setStudyState("completed", x => {
    const l = x || [];
    const newCompleted = {
      trialName: data.trialName,
      repitionIdentifierVariable: data.repitionIdentifierVariable || null,
      repitionIdentifier: data.repitionIdentifierVariable ? data[data.repitionIdentifierVariable] : null,
    }
    return l.concat([newCompleted]);
  });
};

const preloadStatus = {}
const backgroundPreload = (preloadSpec) => {
  const makeCallbacks = (fileType) => {
    const onComplete = () => {};
    const onSingleComplete = (file) => {
      preloadStatus[file] = true;
    };
    const onError = (file) => {
      crashWithError(Error(`Failed to preload ${fileType} file: ${file}`));
    };

    return [ onComplete, onSingleComplete, onError ];
  };
  for (const file of [...preloadSpec.audio, ...preloadSpec.video, ...preloadSpec.images]) {
    preloadStatus[file] = false;
  }
  jsPsych.pluginAPI.preloadAudio(preloadSpec.audio, ...makeCallbacks("audio"));
  jsPsych.pluginAPI.preloadVideo(preloadSpec.video, ...makeCallbacks("video"));
  jsPsych.pluginAPI.preloadImages(preloadSpec.images, ...makeCallbacks("images"));
};


/* === Page reload / already completed functionality === */
const includeIfNotCompleted = async (trial) => {
  const completed = await getStudyState("completed", []);
  if (trial.data?.repitionIdentifierVariable) {
    throw new Error("includeIfNotCompleted cannot handle trials with repitionIdentifierVariable. Use generateMissingProcedure instead.");
  }
  const isCompleted = completed.find(c => c.trialName === trial.data?.trialName);
  return Boolean(isCompleted) ? [] : [trial];
};

const filterForMissing = async (allItems, timeline) => {
  const timelineDetails = timeline.map(t => ({ trialName: t.data?.trialName, repitionIdentifierVariable: t.data?.repitionIdentifierVariable || null }));
  const completed = await getStudyState("completed", []);
  // Filter out items that have already been completed for all timeline entries
  return allItems.filter(item => {
    const alreadyCompleted = timelineDetails.every(td => {
      return completed.find(c => {
        return c.trialName === td.trialName &&
               c.repitionIdentifierVariable === td.repitionIdentifierVariable &&
               (td.repitionIdentifierVariable === null || c.repitionIdentifier === item[td.repitionIdentifierVariable]);
      });
    });
    return !Boolean(alreadyCompleted);
  });
};


/* === Condition assignment (A/B balancing) === */
const ensureConditionAB = async () => {
  const jatos = window.jatos;

  const createIfMissing = async () => {
    // Prepare Batch Session structure if missing
    if (!jatos.batchSession.defined("/counts")) {
      await jatos.batchSession.add("/counts", { A: 0, B: 0 });
    }
  };


  // Compute balanced condition from current counts
  const calculateAssignment = async () => {
    const counts = jatos.batchSession.find("/counts");
    return counts.A === counts.B ? (Math.random() < 0.5 ? "A" : "B") : counts.A < counts.B ? "A" : "B";
  };

  // Write assignment (with simple retry to handle rare race conditions)
  const commitAssignment = async (condition) => {
    const ts = Date.now();
    // Save to result data which will be analyzed in the end, use 'trialName' for compatibility with the other data
    await appendResultJson({ trialName: "assignCondition", assignmentCondition: condition, assignmentTimestamp: ts });
    await setStudyState("condition", () => condition);

    // Increment the bucket's count using replace
    const freshCounts = jatos.batchSession.find("/counts") || { A: 0, B: 0 };
    const next = (freshCounts[condition] || 0) + 1;
    await jatos.batchSession.replace(`/counts/${condition}`, next);
  };

  let condition = await getStudyState("condition", null);

  if (condition) {
    console.log(`Reusing existing condition from Study Session: ${condition}`);
    return condition;
  }

  try {
    condition = await calculateAssignment();
  } catch (e) {
    await createIfMissing();
    condition = await calculateAssignment();
  }
  await commitAssignment(condition);
  console.log(`Assigned new condition: ${condition}`);
  return condition;
};


/* === Initialize === */
const isJATOS = typeof window.jatos !== "undefined";
if (!isJATOS) {
  alert("An error occurred while initializing the experiment. Please try again later. (Code: No JATOS)");
}
window.onbeforeunload = () => {
    return "Are you sure you want to leave? Some progress might be lost.";
};
const jsPsych = initJsPsych({
  show_progress_bar: true,
  on_data_update: onDataUpdate,
});


/*
*** EXPERIMENT TIMELINE DEFINITIONS ***
*/
/* Welcome message */
const welcomeConsentPage = {
    type: jsPsychSurveyHtmlForm,
    data: {
      trialName: "welcomeConsent"
    },
    dataAsArray: true,
    preamble: `
      <div class="custom-content-container">
        ${welcomeConsentHtml}
      </div>
    `,
    html: `
      <label style="font-weight: bold;">
        <input type="checkbox" name="consent" value="yes" required>
        ${consentCheckText}
      </label>
      <br><br>
    `
  };



/* === Demographics === */
const demographicsPage = {
  type: jsPsychSurveyHtmlForm,
  data: {
      trialName: "demographics"
  },
  dataAsArray: true,
  preamble: '<p>Information about you</p>',
  html: `
    <label for="age">Age:</label>
    <select name="age" id="age" required>
      <option value="" disabled selected>Select your age range</option>
      ${[
        "18-24",
        "25-34",
        "35-44",
        "45-54",
        "55-64",
        "65+"
      ].map(interval => `<option value="${interval}">${interval}</option>`).join('')}
    </select>
    <br><br>
    <label for="gender">Gender:</label>
    <select name="gender" id="gender" required>
      <option value="" disabled selected>Select your gender</option>
      <option value="female">Female</option>
      <option value="male">Male</option>
      <option value="other">Other</option>
      <option value="prefer-not-to-say">Prefer not to say</option>
    </select>
    <br><br>
  `
}; // TODO: Add country


/* === DMQ Questionnaire === */
// From https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-clinicians-researchers
const dmqIntro = `
The following questions refer to the experience of being intensely bothered by a sound or sounds, even when they are not overly loud. These can be human or non-human sounds, or the sight of someone or something making a sound that you can't hear (e.g., the sight of someone biting their nails from across the room).
`;

const dmqLikertScale = [
  "Never",
  "Rarely",
  "Sometimes",
  "Often",
  "Always/almost always"
];

const dmqInstructionCognitive = "In the past month on average, when intensely bothered by a sound or sounds, please rate how often you had each of the following thoughts.";
const dmqQuestionsCognitive = [
  "I am helpless",
  "I want to cry",
  "How do I make this sound stop?",
  "Everything is awful.",
  "I cannot handle this",
  "I need to get away from the sound.",
  "I would do anything to make it stop.",
  "I thought about screaming at, yelling at, or telling off the person making the sound.",
  "I thought about pushing, poking, shoving, etc. the person making the sound.",
  "I thought about physically hurting the person making the sound.",
];

const dmqInstructionPhysiological = "In the past month on average, when intensely bothered by a sound or sounds, please rate how often each of the following happened to you.";
const dmqQuestionsPhysiological = [
  "I became rigid or stiff.",
  "I trembled or shuddered.",
  "My heart pounded or raced.",
  "I started breathing intensely or forcefully.",
  "I reflexively jumped.",
];

const dmqInstructionAffective = "In the past month on average, when intensely bothered by a sound or sounds, please rate how often you felt each of the following:";
const dmqQuestionsAffective = [
  "I felt angry.",
  "I felt anxious.",
  "I felt disgusted.",
  "I felt panic.",
  "I felt hostile.",
  "I felt jittery.",
  "I felt frustrated.",
];

const dmqPage = {
  type: jsPsychSurveyLikert,
  data: {
      trialName: "dmq",
      subscale: jsPsych.timelineVariable("subscale"),
      repitionIdentifierVariable: "subscale",
  },
  preamble: () => `
    <p class="dmq-intro">${dmqIntro}</p>
    <p><b>${jsPsych.evaluateTimelineVariable("instructions")}</b></p>
  `,
  questions: () => jsPsych.evaluateTimelineVariable("questions").map(question => {
    return {
      prompt: question,
      name: question,
      labels: dmqLikertScale,
      required: true
    };
  }),
  randomize_question_order: false
};

const generateDMQProcedure = async () => {
  const dmqTimeline = [dmqPage];
  const missingDMQ = await filterForMissing( [
      { subscale: "affective", instructions: dmqInstructionAffective, questions: dmqQuestionsAffective },
      { subscale: "physiological", instructions: dmqInstructionPhysiological, questions: dmqQuestionsPhysiological },
      { subscale: "cognitive", instructions: dmqInstructionCognitive, questions: dmqQuestionsCognitive },
    ], dmqTimeline);
  if (missingDMQ.length === 0) {
    return [];
  }
  return [{
      timeline: dmqTimeline,
      timeline_variables: missingDMQ,
  }];

};


/* === Helpers for trigger category selection === */
const makeTriggerCategoryFieldset = (triggerCategories, legend) => `
  <fieldset class="rating-fieldset" style="margin-top:2rem;" aria-labelledby="cat-legend">
    <legend class="rating-legend" id="cat-legend">
      ${legend}
    </legend>

    <p class="rating-hint">Select one or more options.</p>

    <input type="hidden" name="trigger_categories" id="trigger-categories-hidden" required />
    <input type="text" id="trigger-categories" name="trigger_categories" required autocomplete="off" class="visually-hidden-validator" />

    <div class="rating-stack" role="group" aria-label="Sound category (choose one or more)">
      ${triggerCategories.map((cat, i) => {
        const id = `cat-${i}`;
        const isNone = cat === "None of the above";
        return `
          <div class="rating-option">
            <input class="rating-input category-input" type="checkbox"
                    id="${id}" value="${cat}" data-none="${isNone ? '1' : '0'}" />
            <label class="rating-label" for="${id}">
              <span class="rating-text">${cat}</span>
            </label>
          </div>`;
      }).join("")}
    </div>
  </fieldset>
`;
const triggerCategoryOnLoad = () => {
  const hidden = document.getElementById('trigger-categories');
  const boxes = Array.from(document.querySelectorAll('.category-input'));
  const noneBox = boxes.find(b => b.dataset.none === '1');

  function syncState(changed) {
    // Enforce “None of the above” mutual exclusivity
    if (changed && changed === noneBox && noneBox.checked) {
      boxes.forEach(b => { if (b !== noneBox) b.checked = false; });
    } else if (changed && changed !== noneBox && changed.checked) {
      if (noneBox) noneBox.checked = false;
    }

    // Collect selected values
    const selected = boxes.filter(b => b.checked).map(b => b.value);

    // Required: at least one selected
    if (selected.length === 0) {
      hidden.value = "";
      hidden.setCustomValidity("Please select at least one category.");
    } else {
      hidden.value = JSON.stringify(selected); // saved as a JSON array string
      hidden.setCustomValidity("");
    }
  }

  boxes.forEach(b => b.addEventListener('change', () => syncState(b)));
  // Initialize validity on page load
  syncState(null);
}


/* === Trigger declaration === */
const triggerDeclarePage = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trialName: "triggerDeclaration",
  },
  preamble: `
    <p class="dmq-intro">${dmqIntro}</p>
  `,
  html: makeTriggerCategoryFieldset(triggerCategories.concat(["Others", "None of the above"]), "Select the sounds and/or sights that bother you much more intensely than they do most other people."),
  on_load: triggerCategoryOnLoad,
};


/* === Stimulus presentation and rating === */

/* = Stimulus preload = */
const stimulusPreloadPage = {
  type: jsPsychCallFunction,
  data: {
    doNotSave: true,
    trialName: "stimulusPreload",
    stimulusId: jsPsych.timelineVariable("stimulusId"),
    repitionIdentifierVariable: "stimulusId",
    wavUrl: jsPsych.timelineVariable("wavUrl"),
  },
  async: true,
  func: async (done) => {
    // Set loading message
    document.querySelector("#jspsych-content").innerHTML = `
      <div class="custom-content-container">
        <p>Loading sound, please wait...</p>
        <div style="max-height:1px;overflow:hidden;">
          ${soundPlayingHtml}
        </div>
      </div>
    `;

    // Wait for all to be preloaded
    const wavUrl = jsPsych.evaluateTimelineVariable("wavUrl");
    while (!preloadStatus[wavUrl] ||
           !preloadStatus[soundPlayingMp4] ||
           !preloadStatus[soundPlayingGif]) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    document.querySelector("#jspsych-root").innerHTML = ``;
    done({});
  }
}


/* = Stimulus presentation = */
const soundPlayingHtml = `
  <p>Please listen to the sound playing</p>
  <video nocontrols autoplay loop muted playsinline style="width:100%;height:auto;max-width: 12rem;">
    <source src="${soundPlayingMp4}" type="video/mp4">
    <img src="${soundPlayingGif}" alt="Sound playing animation">
  </video>
`;
const stimulusPresentPage = {
    type: jsPsychAudioButtonResponse,
    data: {
      trialName: "stimuliPresentation",
      stimulusId: jsPsych.timelineVariable("stimulusId"),
      repitionIdentifierVariable: "stimulusId",
    },
    stimulus: jsPsych.timelineVariable("wavUrl"),
    trial_duration: 30000,
    choices: ['Sound is too uncomfortable, stop playback'],
    prompt: soundPlayingHtml,
};

/* = Stimulus rating = */
const stimulusRatingButtons = [
  { label: "5", color: "#e20001" },
  { label: "4", color: "#e25800" },
  { label: "3", color: "#e8b30f" },
  { label: "2", color: "#e2d70b" },
  { label: "1", color: "#97e600" },
  { label: "0", color: "#2ae204" },
];
const stimulusRatePage = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trialName: "stimulusRating",
    stimulusId: jsPsych.timelineVariable("stimulusId"),
    repitionIdentifierVariable: "stimulusId",
    wavUrl: jsPsych.timelineVariable("wavUrl")
  },
  html: () =>  `
    <fieldset class="rating-fieldset">
      <legend class="rating-legend">
        Rate the discomfort/anxiety you felt while hearing the sound
      </legend>

      <p class="rating-hint">Very much discomfort</p>

      <div class="rating-stack" role="radiogroup" aria-label="Discomfort rating">
        ${stimulusRatingButtons.map((btn, i) => {
          const id = `rate-${i}`;
          // Per HTML spec, “required” on ONE radio within the group makes the whole group required
          // (we set it on the first input).
          const required = i === 0 ? "required" : "";
          return `
            <div class="rating-option">
              <input class="rating-input" type="radio" name="stimuli_rating" id="${id}"
                    value="${btn.label}" ${required} />
              <label class="rating-label" for="${id}" style="--rating-color: ${btn.color}">
                <span class="rating-circle" aria-hidden="true"></span>
                <span class="rating-text">${btn.label}</span>
              </label>
            </div>`;
        }).join("")}
      </div>

      <p class="rating-hint">Very little discomfort</p>
    </fieldset>


    ${
      makeTriggerCategoryFieldset(
        triggerCategories.concat(["None of the above"]),
        "Which of the following categories did the sound you just heard belong to?"
      )
    }
  `,
  button_label: "Play next sound",
  on_load: triggerCategoryOnLoad,
};

/* = Stimulus procedure timeline = */
const stimulusProcedureTimeline = [stimulusPreloadPage, stimulusPresentPage, stimulusRatePage];
const generateStimulusPresentation = async (missingStimuli) => {
  const firstAnchorStimuli = missingStimuli.filter(s => s.anchorPosition === "first");
  const lastAnchorStimuli = missingStimuli.filter(s => s.anchorPosition === "last");
  const nonAnchorStimuli = missingStimuli.filter(s => !s.anchorPosition);

  const stimuliTimelinePart = [];

  if (firstAnchorStimuli.length > 0) {
    stimuliTimelinePart.push({
      timeline: stimulusProcedureTimeline,
      data: {
        isFirstAnchor: true,
      },
      timeline_variables: firstAnchorStimuli,
    });
  }

  if (nonAnchorStimuli.length > 0) {
    stimuliTimelinePart.push({
      timeline: stimulusProcedureTimeline,
      randomize_order: true,
      timeline_variables: nonAnchorStimuli,
    });
  }

  if (lastAnchorStimuli.length > 0) {
    stimuliTimelinePart.push({
      timeline: stimulusProcedureTimeline,
      data: {
        isLastAnchor: true,
      },
      timeline_variables: lastAnchorStimuli,
    });
  }

  if (stimuliTimelinePart.length > 0) {
    stimuliTimelinePart.unshift(
      {
        type: jsPsychHtmlButtonResponse,
        data: {
          doNotSave: true,
          trialName: "stimuliInstructions",
        },
        stimulus: `
          <div class="custom-content-container">
            ${stimuliPresentationInstructionsHtml}
          </div>
        `,
        choices: ["Play sound"],
      }
    );
  }

  return stimuliTimelinePart;
};


/* === Thank you page === */
const thanksPage = {
  type: jsPsychCallFunction,
  data: {
    trialName: "thanks",
  },
  async: true,
  func: async () => {
    window.onbeforeunload = null; // Disable the warning on unload
    const shareLink = getShareLink();
    document.querySelector("#jspsych-content").innerHTML = `
      <div class="custom-content-container">
        <h1>Thank You!</h1>
        <p>Your participation is greatly appreciated.</p>
        <p>If you would like to share this study with others, please share the following link:</p>
        <div style="display:flex;gap:.5rem;align-items:center">
          <input id="study-link" value="${shareLink}" style="flex:1;padding:.6rem;border:1px solid #ddd;border-radius:8px" readonly />
          <button id="copy-btn" style="padding:.6rem 1rem;border:0;border-radius:8px;cursor:pointer">
            Copy
          </button>
        </div>

        <p>
          If you are interested in learning more about the condition, see <a href="https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-sufferers-loved-ones" target="_blank">the list of resources made by the Duke Center for Misophonia and Emotion Regulation</a>.
        </p>

        <p>
          ${contactInfo}
        </p>

        <p>You can now close this window.</p>

        <div class="copyright-credits">
          ${copyrightCredits}
        </div>
      </div>
    `;
    const copyBtn = document.getElementById('copy-btn');
    const input = document.getElementById('study-link');
    copyBtn?.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(input.value);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => (copyBtn.textContent = 'Copy'), 1200);
      } catch (_) {
        input.select(); document.execCommand('copy');
      }
    });
    // On select, select all text
    input?.addEventListener('focus', (event) => {
      event.target.select();
    });

    // await window.jatos.endStudyWithoutRedirect(); // Do not mark complete to allow revisiting the thank you page
  }
};


/*
*** EXPERIMENT TIMELINE INITIALIZATION AND RUNNING THE EXPERIMENT ***
*/
window.jatos.onLoad(async () => {
  console.log("JATOS is loaded");
  document.querySelector("#jatos-waiting-message").style.display = "none";
  const shareLink = getShareLink();
  ensureOneBrowserPerStudy((new URL(shareLink)).pathname);

  const condition = await ensureConditionAB();
  const allStimuliForCondition = stimuliAB[condition];
  const missingStimuli = await filterForMissing(allStimuliForCondition, stimulusProcedureTimeline);

  const filesToPreload = {
    audio: missingStimuli.map(s => s.wavUrl),
    video: [soundPlayingMp4],
    images: [soundPlayingGif],
  };
  backgroundPreload(filesToPreload);

  console.log(`Completed stimuli:`, allStimuliForCondition.length - missingStimuli.length);
  console.log(`Files to preload:`, filesToPreload);

  const timeline = [
    ...await includeIfNotCompleted(welcomeConsentPage),
    ...await includeIfNotCompleted(demographicsPage),
    ...await includeIfNotCompleted(triggerDeclarePage),
    ...await generateDMQProcedure(),
    ...await generateStimulusPresentation(missingStimuli),
    thanksPage
  ];

  console.log("Final timeline:", timeline);

  jsPsych.run(timeline);
});


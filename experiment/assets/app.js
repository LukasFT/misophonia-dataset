const stimuli = [
  { stimulus_id: "phrases2b20" },
  { stimulus_id: "Haircut16-44p1" },
];
stimuli.forEach(s => s.wav_url = `sounds/${s.stimulus_id}.wav`);


const preload = {
    type: jsPsychPreload,
    auto_preload: true
};

window.onbeforeunload = function() {
    return "Are you sure you want to leave? Your progress will NOT be saved.";
}

const on_data_update = (data) => {
  const jsonData = JSON.stringify(data);
  console.log(`Data updated: ${jsonData}`);

  window.jatos.appendResultData(jsonData);
};


const jsPsych = initJsPsych({
  show_progress_bar: true,
  on_data_update: on_data_update,
});


const consent_instructions_page = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trial_name: "consent_instructions_page"
  },
  dataAsArray: true,
  preamble: `
  <h1>Misophonia Study</h1>
  <p>Lorem ipsum ....</p>
  <h1>Consent</h1>
  `,
  html: `
    <label>
      <input type="checkbox" name="consent" value="yes" required>
      I am 18 years or older, I have read and understood the information provided, and I consent to participate in this study.
    </label>
    <br><br>
  `
};

const demographics_page = {
  type: jsPsychSurveyHtmlForm,
  data: {
      trial_name: "demographics_page"
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
};


const dmq_likert_scale = [
  "Strongly Disagree",
  "Disagree",
  "Neutral",
  "Agree",
  "Strongly Agree"
];

const dmq_quiestions = [
  "Some question 1",
  "Some question 2",
  "Some question 3",
  "Some question 4",
  "Some question 5",
  "Some question 6",
  "Some question 7",
  "Some question 8",
  "Some question 9",
  "Some question 10",
]

const dmq_page = {
  type: jsPsychSurveyLikert,
  data: {
      trial_name: "dmq_page"
  },
  preamble: `
    <h1>Misophonia Assessment</h1>
    <p>Please indicate your level of agreement with the following questions.</p>
  `,
  questions: dmq_quiestions.map(question => {
    return {
      prompt: question,
      name: question,
      labels: dmq_likert_scale,
      required: true
    };
  }),
  randomize_question_order: false
};


const stimulusPresentPage = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trial_name: "stimuli_presentation",
    stimulus: jsPsych.timelineVariable("stimulus")
  },
  dataAsArray: true,
  preamble: () => `<p>Stimuli: ${jsPsych.evaluateTimelineVariable("stimulus")}</p>`,
  html: `
    <p>Placeholder for stimuli presentation.</p>
  `
};


const stimulusRatePage = {
  type: jsPsychSurveyLikert,
  data: {
    trial_name: "stimuli_rate_page",
    stimulus: jsPsych.timelineVariable("stimulus")
  },
  preamble: `
    <h1>Placeholder for stimuli rating</h1>
    <p>Placeholder for stimuli rating.</p>
  `,
  questions: [{
      prompt: "Please rate the stimuli you just experienced.",
      name: "stimuli_rating",
      labels: dmq_likert_scale,
      required: true
  }],
};

const stimulusProcedureTimeline = [stimulusPresentPage, stimulusRatePage];
const stimulusProcedure = {
  timeline: stimulusProcedureTimeline,
  randomize_order: true,
  timeline_variables: stimuli.map(s => ({ stimulus: s.wav_url })),
};

const anchorCtrlStimulusProcedure = {
  timeline: stimulusProcedureTimeline,
  timeline_variables: [
    { stimulus: "ctrl-anchor" },
  ],
};

const anchorTrigStimulusProcedure = {
  timeline: stimulusProcedureTimeline,
  timeline_variables: [
    { stimulus: "trig-anchor" },
  ],
};

const thanksPage = {
  type: jsPsychCallFunction,
  data: {
    trial_name: "thanks_page",
  },
  func: async () => {
    window.onbeforeunload = null; // Disable the warning on unload
    const getShareLink = () => {
      const code = window.jatos.studyCode;
      const origin = window.location.origin;
      return `${origin}/publix/${code}`;

    }
    const shareLink = getShareLink();
    document.querySelector("#jspsych-root").innerHTML = `
    <div style="max-width:600px;margin:2rem auto;font-family:sans-serif;padding:20px;">
      <h1>Thank You!</h1>
      <p>Your participation is greatly appreciated.</p>
      <p>If you would like to share this study with others, please share the following link:</p>
      <div style="display:flex;gap:.5rem;align-items:center">
        <input id="study-link" value="${shareLink}" style="flex:1;padding:.6rem;border:1px solid #ddd;border-radius:8px" readonly />
        <button id="copy-btn" style="padding:.6rem 1rem;border:0;border-radius:8px;cursor:pointer">
          Copy
        </button>
      </div>
      </p>
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

    await window.jatos.appendResultData(JSON.stringify({ finalized: true }));
    await window.jatos.endStudyWithoutRedirect();

  }
};


const isJATOS = typeof window.jatos !== "undefined";
if (!isJATOS) {
  alert("An error occurred while initializing the experiment. Please try again later. (Code: No JATOS)");
}

const ensureConditionAB = async () => {
  const jatos = window.jatos;

  const createIfMissing = async () => {
    // Prepare Batch Session structure if missing
    if (!jatos.batchSession.defined("/counts")) {
      await jatos.batchSession.add("/counts", { A: 0, B: 0 });
    }
    if (!jatos.batchSession.defined("/assignments")) {
      await jatos.batchSession.add("/assignments", {});
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
    // Write this worker's assignment
    await jatos.batchSession.add(`/assignments/${jatos.workerId}`, { condition, ts });
    // Increment the bucket's count using replace
    const freshCounts = jatos.batchSession.find("/counts") || { A: 0, B: 0 };
    const next = (freshCounts[condition] || 0) + 1;
    await jatos.batchSession.replace(`/counts/${condition}`, next);
  };

  // If already in Study Session, reuse it
  const ss = jatos.studySessionData || {};
  if (ss.condition) {
    console.log(`Reusing existing condition from Study Session: ${ss.condition}`);
    return ss.condition;
  }

  let condition;
  try {
    condition = await calculateAssignment();
  } catch (e) {
    await createIfMissing();
    condition = await calculateAssignment();
  }
  await commitAssignment(condition);
  console.log(`Assigned new condition: ${condition}`);
  await jatos.setStudySessionData({ condition });
  return condition;
}

window.jatos.onLoad(async () => {
  console.log("JATOS is loaded");
  document.querySelector("#jatos-waiting-message").style.display = "none";

  const condition = await ensureConditionAB();
  const firstAnchor = condition === "A" ? anchorCtrlStimulusProcedure : anchorTrigStimulusProcedure;
  const secondAnchor = condition === "A" ? anchorTrigStimulusProcedure : anchorCtrlStimulusProcedure;

  const timeline = [
    consent_instructions_page,
    // demographics_page,
    // dmq_page,
    // firstAnchor,
    stimulusProcedure,
    // secondAnchor,
    thanksPage
  ];
  // drip save
  jsPsych.run(timeline);

});




// // Minimal timeline example with per-trial append + resume via Study Session data

// // ----- deterministic RNG helpers (for rebuild on reload) -----
// function hashToInt(str) {
//   let h = 2166136261 >>> 0;
//   for (let i = 0; i < str.length; i++) {
//     h ^= str.charCodeAt(i);
//     h = Math.imul(h, 16777619);
//   }
//   return h >>> 0;
// }
// function mulberry32(a) {
//   return function () {
//     let t = (a += 0x6D2B79F5);
//     t = Math.imul(t ^ (t >>> 15), t | 1);
//     t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
//     return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
//   };
// }
// function shuffleWithRng(array, rng) {
//   const arr = array.slice();
//   for (let i = arr.length - 1; i > 0; i--) {
//     const j = Math.floor(rng() * (i + 1));
//     [arr[i], arr[j]] = [arr[j], arr[i]];
//   }
//   return arr;
// }

// // ----- jsPsych init with per-trial append -----
// const jsPsych = initJsPsych({
//   display_element: "jspsych-root",
//   on_data_update: (trialData) => {
//     // Append only the new trial's data (small payload)
//     return jatos.appendResultData(JSON.stringify(trialData));
//   }
// });

// // ----- Build (or rebuild) the timeline after JATOS is ready -----
// jatos.onLoad(async () => {
//   // Initialize session progress and seed on first load
//   if (!jatos.studySessionData || !jatos.studySessionData.progress) {
//     jatos.studySessionData = {
//       progress: { trial_index: 0 },
//       seed: Math.random().toString(36).slice(2)
//     };
//     await jatos.setStudySessionData(jatos.studySessionData);
//   }

//   // Deterministic ordering with seed so we can reconstruct on reload
//   const rng = mulberry32(hashToInt(jatos.studySessionData.seed));

//   // Example stimuli; replace with your trials
//   const baseTrials = [
//     { type: "html-button-response", stimulus: "<p>Screen 1</p>", choices: ["Next"] },
//     { type: "html-button-response", stimulus: "<p>Screen 2</p>", choices: ["Next"] },
//     { type: "html-button-response", stimulus: "<p>Screen 3</p>", choices: ["Finish"] }
//   ];

//   const timelineOrdered = shuffleWithRng(baseTrials, rng);

//   // Resume from last completed trial index
//   const startAt = jatos.studySessionData.progress.trial_index || 0;
//   const remaining = timelineOrdered.slice(startAt);

//   // After each trial finishes, bump the cursor and persist session data
//   jsPsych.pluginAPI.registerPreload("html-button-response", "stimulus", "html");
//   jsPsych.options.on_trial_finish = async () => {
//     jatos.studySessionData.progress.trial_index = (jatos.studySessionData.progress.trial_index || 0) + 1;
//     await jatos.setStudySessionData(jatos.studySessionData);
//   };

//   await jsPsych.run(remaining);

//   // Finalize (optional: submit a final aggregate snapshot)
//   await jatos.appendResultData(JSON.stringify({ finalized: true, ntrials: timelineOrdered.length }));
//   await jatos.endStudy();
// });

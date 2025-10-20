const preload = {
    type: jsPsychPreload,
    auto_preload: true
}

const jsPsych = initJsPsych({
  show_progress_bar: true,
});


const consent_instructions_page = {
  type: jsPsychSurveyHtmlForm,
  dataAsArray: true,
  preamble: '<p><b>Consent</b></p>',
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




jsPsych.run([consent_instructions_page, demographics_page, dmq_page]);

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

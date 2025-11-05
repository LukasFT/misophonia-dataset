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
Object.values(stimuliAB).forEach(g => {
  g.forEach(s => {
    s.wavUrl = `sounds/${s.stimulusId}.wav`
  });
});

const triggerCategories = [
  "Category A",
  "Category B",
  "Category C",
  "Category D",
]


window.onbeforeunload = function() {
    return "Are you sure you want to leave? Your progress will NOT be saved.";
}


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

const onDataUpdate = async (data) => {
  await setStudyState("completed", x => {
    const l = x || [];
    const newCompleted = {
      trialName: data.trialName,
      repitionIdentifierVariable: data.repitionIdentifierVariable || null,
      repitionIdentifier: data.repitionIdentifierVariable ? data[data.repitionIdentifierVariable] : null,
    }
    return l.concat([newCompleted]);
  });
  if (data.doNotSave) return; // skip non-essential data
  const jsonData = JSON.stringify(data);
  console.log(`Data updated: ${jsonData}`);

  window.jatos.appendResultData(jsonData);
};


const jsPsych = initJsPsych({
  show_progress_bar: true,
  on_data_update: onDataUpdate,
});

const welcomeHtml = `
  <h1>Misophonia Study</h1>

  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eros tellus, congue ut aliquet vel, ullamcorper ut ipsum. In hac habitasse platea dictumst. Curabitur auctor interdum nibh ut molestie. Pellentesque ac sapien nisi. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Curabitur sed sagittis dolor, id egestas felis. Maecenas sollicitudin id sapien sed accumsan. Sed molestie posuere molestie. Nam ac ipsum dapibus, vestibulum purus et, consequat quam. Nunc dictum felis non pharetra rhoncus. Sed nec rhoncus urna. Maecenas luctus tellus non metus consequat ornare. Fusce nec leo sem. Pellentesque lobortis sapien eu dui auctor porta. Vestibulum sagittis, ex eu suscipit bibendum, ante leo tincidunt risus, luctus ornare orci tellus id lorem. </p>
`;



const welcomePage = {
  type: jsPsychHtmlButtonResponse,
  data: {
    doNotSave: true,
    trialName: "welcome",
  },
  stimulus: welcomeHtml,
  choices: ["Continue"],
};

const consentInstructionsPage = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trialName: "consentInstructions"
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


// From https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-clinicians-researchers
const dmqIntro = `
The following questions refer to the experience of being intensely bothered by a sound or sounds, even when they are not overly loud. These can be human or non-human sounds, or the sight of someone or something making a sound that you can't hear (e.g., the sight of someone biting their nails from across the room).
`

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
}

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
    prompt: "<p>Close your eyes and listen to the sound.</p>"
};



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


    ${makeTriggerCategoryFieldset(triggerCategories.concat(["None of the above"]), "Which of the following categories did the sound you just heard belong to?")}
  `,
  on_load: triggerCategoryOnLoad,
};

const stimulusProcedureTimeline = [stimulusPresentPage, stimulusRatePage];


const thanksPage = {
  type: jsPsychCallFunction,
  data: {
    trialName: "thanks",
    doNotSave: true,
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
    <div style="max-width:600px;margin:2rem auto;font-family:sans-serif;">
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
        <a href="https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-sufferers-loved-ones" target="_blank">Read more about Misophonia on Duke Center for Misophonia and Emotion Regulation</a>.
      </p>


      <p>You can now close this window.</p>
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
    // await window.jatos.endStudyWithoutRedirect();

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
  await setStudyState("condition", () => condition);
  return condition;
};

// const getMissingStimuli = async (allStimuliForCondition) => {
//   const completed = await getStudyState("completed", []);
//   return allStimuliForCondition.filter(s => {
//     const alreadyCompleted = completed.find(c => {
//       return c.trialName === "stimulusRating" &&
//              c.repitionIdentifier === s[c.repitionIdentifierVariable];
//     });
//     return !Boolean(alreadyCompleted);
//   });
// };



const generateSimulusPresentation = async (missingStimuli) => {
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

  return stimuliTimelinePart;
};


window.jatos.onLoad(async () => {
  console.log("JATOS is loaded");
  document.querySelector("#jatos-waiting-message").style.display = "none";

  const condition = await ensureConditionAB();
  const allStimuliForCondition = stimuliAB[condition];
  const missingStimuli = await filterForMissing(allStimuliForCondition, stimulusProcedureTimeline);

  console.log(`Total stimuli for condition:`, allStimuliForCondition);
  console.log(`Completed stimuli:`, allStimuliForCondition.length - missingStimuli.length);
  console.log(`Missing stimuli:`, missingStimuli);

  const preloadWelcome = {
    type: jsPsychPreload,
    data: {
      doNotSave: true,
      trialName: "preloadWelcome",
    },
    auto_preload: false, // specify files manually
    audio: missingStimuli.map(s => s.wavUrl),
    // continue_after_error: true, // There is an error with this when errors occur ...
    message: `
    ${welcomeHtml}
    <p>Loading experiment assets, please wait...</p>
    `,
};

  

  const timeline = [
    // preloadWelcome,
    // welcomePage,
    ...await includeIfNotCompleted(consentInstructionsPage),
    ...await includeIfNotCompleted(demographicsPage),
    ...await includeIfNotCompleted(triggerDeclarePage),
    ...await generateDMQProcedure(),
    ...await generateSimulusPresentation(missingStimuli),
    thanksPage
  ];

  jsPsych.run(timeline);

});




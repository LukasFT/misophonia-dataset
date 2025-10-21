const stimuliAB = {
  A: [
    { stimulus_id: "phrases2b20" },

    { stimulus_id: "Haircut16-44p1-2", anchor_position: "first" },
    { stimulus_id: "Haircut16-44p1", anchor_position: "last" }
  ],
  B: [
    { stimulus_id: "phrases2b20" },

    { stimulus_id: "Haircut16-44p1", anchor_position: "last" },
    { stimulus_id: "Haircut16-44p1", anchor_position: "first" }
  ],
};
Object.values(stimuliAB).forEach(g => {
  g.forEach(s => {
    s.wav_url = `sounds/${s.stimulus_id}.wav`
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

const on_data_update = (data) => {
  if (data.do_not_save) return; // skip non-essential data
  const jsonData = JSON.stringify(data);
  console.log(`Data updated: ${jsonData}`);

  window.jatos.appendResultData(jsonData);
};


const jsPsych = initJsPsych({
  show_progress_bar: true,
  on_data_update: on_data_update,
});

const welcomeHtml = `
  <h1>Misophonia Study</h1>

  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eros tellus, congue ut aliquet vel, ullamcorper ut ipsum. In hac habitasse platea dictumst. Curabitur auctor interdum nibh ut molestie. Pellentesque ac sapien nisi. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Curabitur sed sagittis dolor, id egestas felis. Maecenas sollicitudin id sapien sed accumsan. Sed molestie posuere molestie. Nam ac ipsum dapibus, vestibulum purus et, consequat quam. Nunc dictum felis non pharetra rhoncus. Sed nec rhoncus urna. Maecenas luctus tellus non metus consequat ornare. Fusce nec leo sem. Pellentesque lobortis sapien eu dui auctor porta. Vestibulum sagittis, ex eu suscipit bibendum, ante leo tincidunt risus, luctus ornare orci tellus id lorem. </p>
`;



const welcomePage = {
  type: jsPsychHtmlButtonResponse,
  data: {
    do_not_save: true,
  },
  stimulus: welcomeHtml,
  choices: ["Continue"],
};

const consent_instructions_page = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trial_name: "consent_instructions"
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
      trial_name: "demographics"
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
      trial_name: "dmq",
      dmq_subscale: jsPsych.timelineVariable("subscale")
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

const dmqProcedure = {
  timeline: [dmqPage],
  timeline_variables: [
    { subscale: "affective", instructions: dmqInstructionAffective, questions: dmqQuestionsAffective },
    { subscale: "physiological", instructions: dmqInstructionPhysiological, questions: dmqQuestionsPhysiological },
    { subscale: "cognitive", instructions: dmqInstructionCognitive, questions: dmqQuestionsCognitive },
  ]
};


const stimulusPresentPage = {
    type: jsPsychAudioButtonResponse,
    data: {
      trial_name: "stimuli_presentation",
      stimulus_id: jsPsych.timelineVariable("stimulus_id")
    },
    stimulus: jsPsych.timelineVariable("wav_url"),
    trial_duration: 30000,
    choices: ['Sound is too uncofortable, stop playback'],
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
    trial_name: "trigger_declaration",
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
    trial_name: "stimulus_rating",
    stimulus_id: jsPsych.timelineVariable("stimulus_id"),
    wav_url: jsPsych.timelineVariable("wav_url")
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


const thanksPage = {
  type: jsPsychCallFunction,
  data: {
    trial_name: "thanks_page",
    do_not_save: true,
  },
  func: async () => {
    const dmqScore = jsPsych
          .data.get().filter({trial_name: "dmq"}).trials
          .map(t => t.response)
          .reduce((s, o) => s + Object.values(o).reduce((a, v) => a + v, 0), 0);
    const dmqScaleCutoff = 42; // From Rosenthal et al., 2021

    console.log(`DMQ total score: ${dmqScore}`);

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
        The questions you answered ${dmqScore >= dmqScaleCutoff ? "indicate" : "do not indicate"} that you have higher misophonia symptoms severity (DMQ Symptom Severity score of ${dmqScore}).

        <a href="https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-sufferers-loved-ones" target="_blank">Read more on the Duke Center for Misophonia and Emotion Regulation</a>.
      </p>


      <p>You can now close this window. You will not be able to see this page or do the study again.</p>
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
  const stimuli = stimuliAB[condition];

  const preloadWelcome = {
    type: jsPsychPreload,
    data: {
      do_not_save: true,
    },
    auto_preload: false, // specify files manually
    audio: stimuli.map(s => s.wav_url),
    // continue_after_error: true, // There is an error with this when errors occur ...
    message: `
    ${welcomeHtml}
    <p>Loading experiment assets, please wait...</p>
    `,
};

  const stimulusProcedureTimeline = [stimulusPresentPage, stimulusRatePage];
  const stimulusProcedure = {
    timeline: stimulusProcedureTimeline,
    randomize_order: true,
    timeline_variables: stimuli.filter(s => !s.anchor_position),
  };

  const firstAnchor = {
    timeline: stimulusProcedureTimeline,
    data: {
      is_first_anchor: true,
    },
    timeline_variables: stimuli.filter(s => s.anchor_position === "first"),
  };

  const secondAnchor = {
    timeline: stimulusProcedureTimeline,
    data: {
      is_second_anchor: true,
    },
    timeline_variables: stimuli.filter(s => s.anchor_position === "last"),
  };

  const timeline = [
    preloadWelcome,
    welcomePage,
    consent_instructions_page,
    demographics_page,
    triggerDeclarePage,
    dmqProcedure,
    firstAnchor,
    stimulusProcedure,
    secondAnchor,
    thanksPage
  ];

  jsPsych.run(timeline);

});




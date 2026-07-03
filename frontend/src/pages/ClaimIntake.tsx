import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
} from "@mui/material";
import api from "../services/api";

interface IntakeStep {
  step_id: string;
  label: string;
  prompt: string;
  field_type: string;
  options: string[];
  required: boolean;
}

interface ClaimIntake {
  policy_number: string;
  date_of_loss: string;
  time_of_loss: string;
  location: string;
  description: string;
  parties: { name: string; role: string }[];
  damages: { description: string; type: string }[];
  witness_info: string;
  police_report: boolean;
  reported_date: string;
}

const ClaimIntakeForm: React.FC = () => {
  const [steps, setSteps] = useState<IntakeStep[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ClaimIntake | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previousIntakes, setPreviousIntakes] = useState<ClaimIntake[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    api.get("/claims/intake/steps").then((res) => setSteps(res.data));
    api.get("/claims/intake/list").then((res) => setPreviousIntakes(res.data));
  }, []);

  const currentStep = steps[activeStep];
  if (!currentStep) return <CircularProgress />;

  const handleNext = () => {
    if (activeStep < steps.length - 1) setActiveStep((s) => s + 1);
  };

  const handleBack = () => {
    if (activeStep > 0) setActiveStep((s) => s - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.post("/claims/intake/submit", { responses });
      setResult(res.data);
      setPreviousIntakes((prev) => [...prev, res.data]);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to submit intake.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (step: IntakeStep) => {
    const val = responses[step.step_id] || "";

    if (step.field_type === "select") {
      return (
        <FormControl fullWidth>
          <InputLabel>{step.label}</InputLabel>
          <Select
            value={val}
            label={step.label}
            onChange={(e) => setResponses({ ...responses, [step.step_id]: e.target.value })}
          >
            {step.options.map((o) => (
              <MenuItem key={o} value={o}>{o}</MenuItem>
            ))}
          </Select>
        </FormControl>
      );
    }

    if (step.field_type === "textarea") {
      return (
        <TextField
          fullWidth
          multiline
          minRows={3}
          maxRows={6}
          label={step.label}
          placeholder={step.prompt}
          value={val}
          onChange={(e) => setResponses({ ...responses, [step.step_id]: e.target.value })}
        />
      );
    }

    return (
      <TextField
        fullWidth
        type={step.field_type}
        label={step.label}
        placeholder={step.prompt}
        value={val}
        onChange={(e) => setResponses({ ...responses, [step.step_id]: e.target.value })}
      />
    );
  };

  if (result) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Claim Intake Assistant</Typography>
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
              <Typography variant="h6">Claim Recorded</Typography>
              <Chip label="Filed" size="small" color="success" />
            </Box>
            <Typography variant="body2" color="text.secondary">
              Date: {result.date_of_loss} | Location: {result.location}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>{result.description}</Typography>
            <Box sx={{ mt: 1 }}>
              {result.damages.map((d, i) => (
                <Chip key={i} label={`${d.type}: ${d.description.slice(0, 60)}`} size="small" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />
              ))}
            </Box>
          </CardContent>
        </Card>
        <Button variant="outlined" onClick={() => { setResult(null); setResponses({}); setActiveStep(0); }}>
          File Another Claim
        </Button>
        <Button sx={{ ml: 1 }} onClick={() => setShowHistory(!showHistory)}>
          {showHistory ? "Hide" : "Show"} Claim History ({previousIntakes.length})
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Claim Intake Assistant</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Guided step-by-step claim intake. Fill in each section — only required fields are mandatory.
      </Typography>

      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3, overflowX: "auto" }}>
        {steps.map((s, i) => (
          <Step key={i}>
            <StepLabel>{s.label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper variant="outlined" sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          {currentStep.label}
          {currentStep.required && <span style={{ color: "red" }}> *</span>}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {currentStep.prompt}
        </Typography>
        {renderField(currentStep)}
      </Paper>

      <Box sx={{ display: "flex", justifyContent: "space-between" }}>
        <Button disabled={activeStep === 0} onClick={handleBack}>Back</Button>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button variant="outlined" onClick={() => setShowHistory(!showHistory)}>
            {showHistory ? "Hide" : "Show"} History ({previousIntakes.length})
          </Button>
          {activeStep < steps.length - 1 ? (
            <Button variant="contained" onClick={handleNext}>Next</Button>
          ) : (
            <Button variant="contained" onClick={handleSubmit} disabled={submitting}>
              {submitting ? <CircularProgress size={20} /> : "Submit Claim"}
            </Button>
          )}
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      {showHistory && previousIntakes.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mt: 3 }}>
          <Typography variant="h6" gutterBottom>Filed Claims</Typography>
          {previousIntakes.map((intake, i) => (
            <Box key={i} sx={{ py: 1, borderBottom: i < previousIntakes.length - 1 ? "1px solid #eee" : "none" }}>
              <Typography variant="body2">
                {intake.date_of_loss} — {intake.location}
              </Typography>
              <Typography variant="caption" color="text.secondary">{intake.description.slice(0, 120)}</Typography>
            </Box>
          ))}
        </Paper>
      )}
    </Box>
  );
};

export default ClaimIntakeForm;

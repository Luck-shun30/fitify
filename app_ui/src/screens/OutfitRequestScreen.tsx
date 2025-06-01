import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { theme } from '../theme/theme';
import { Card } from '../components/Card';
import { apiService } from '../services/api';

const activities = ['School', 'Work', 'Gym', 'Date', 'Other'];

interface OutfitRequestScreenProps {
  navigation: any;
}

export const OutfitRequestScreen: React.FC<OutfitRequestScreenProps> = ({
  navigation,
}) => {
  const [location, setLocation] = useState('Chicago, US');
  const [selectedActivity, setSelectedActivity] = useState('School');
  const [formality, setFormality] = useState(0.5);
  const [loading, setLoading] = useState(false);

  const getFormalityLabel = (value: number) => {
    if (value < 0.3) return 'Casual';
    if (value < 0.7) return 'Smart Casual';
    return 'Formal';
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const suggestions = await apiService.getOutfitSuggestion({
        location,
        activity: selectedActivity,
        formality: getFormalityLabel(formality),
      });
      
      navigation.navigate('OutfitSuggestions', {
        location,
        activity: selectedActivity,
        formality: getFormalityLabel(formality),
        suggestions,
      });
    } catch (error) {
      console.error('Error getting outfit suggestions:', error);
      // TODO: Show error message to user
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient
      colors={theme.gradients.background}
      style={styles.container}
    >
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Request Outfit</Text>
        </View>

        <Card style={styles.inputCard}>
          <Text style={styles.label}>Location</Text>
          <View style={styles.locationInput}>
            <Ionicons name="location-outline" size={20} color={theme.colors.text} />
            <TextInput
              style={styles.input}
              value={location}
              onChangeText={setLocation}
              placeholder="Enter location"
              placeholderTextColor={theme.colors.textSecondary}
            />
          </View>
        </Card>

        <Card style={styles.inputCard}>
          <Text style={styles.label}>Activity</Text>
          <View style={styles.activityContainer}>
            {activities.map((activity) => (
              <TouchableOpacity
                key={activity}
                style={[
                  styles.activityButton,
                  selectedActivity === activity && styles.selectedActivity,
                ]}
                onPress={() => setSelectedActivity(activity)}
              >
                <Text
                  style={[
                    styles.activityText,
                    selectedActivity === activity && styles.selectedActivityText,
                  ]}
                >
                  {activity}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        <Card style={styles.inputCard}>
          <Text style={styles.label}>Formality Level</Text>
          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={1}
            value={formality}
            onValueChange={setFormality}
            minimumTrackTintColor={theme.colors.primary}
            maximumTrackTintColor={theme.colors.border}
            thumbTintColor={theme.colors.primary}
          />
          <Text style={styles.formalityLabel}>
            {getFormalityLabel(formality)}
          </Text>
        </Card>

        <TouchableOpacity
          style={styles.submitButton}
          onPress={handleSubmit}
          disabled={loading}
        >
          <LinearGradient
            colors={theme.gradients.primary}
            style={styles.buttonGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            {loading ? (
              <ActivityIndicator color={theme.colors.text} />
            ) : (
              <>
                <Text style={styles.buttonText}>Get Suggestions</Text>
                <Ionicons name="arrow-forward" size={24} color={theme.colors.text} />
              </>
            )}
          </LinearGradient>
        </TouchableOpacity>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
    padding: theme.spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  backButton: {
    marginRight: theme.spacing.md,
  },
  title: {
    ...theme.typography.h2,
    color: theme.colors.text,
  },
  inputCard: {
    marginBottom: theme.spacing.lg,
  },
  label: {
    ...theme.typography.h3,
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  locationInput: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    paddingBottom: theme.spacing.sm,
  },
  input: {
    flex: 1,
    marginLeft: theme.spacing.sm,
    color: theme.colors.text,
    ...theme.typography.body,
  },
  activityContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -theme.spacing.xs,
  },
  activityButton: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.borderRadius.md,
    backgroundColor: theme.colors.surface,
    margin: theme.spacing.xs,
  },
  selectedActivity: {
    backgroundColor: theme.colors.primary,
  },
  activityText: {
    ...theme.typography.body,
    color: theme.colors.text,
  },
  selectedActivityText: {
    color: theme.colors.text,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  formalityLabel: {
    ...theme.typography.body,
    color: theme.colors.text,
    textAlign: 'center',
    marginTop: theme.spacing.sm,
  },
  submitButton: {
    marginTop: theme.spacing.lg,
    borderRadius: theme.borderRadius.lg,
    overflow: 'hidden',
    ...theme.shadows.medium,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.lg,
  },
  buttonText: {
    ...theme.typography.h3,
    color: theme.colors.text,
    marginRight: theme.spacing.sm,
  },
}); 
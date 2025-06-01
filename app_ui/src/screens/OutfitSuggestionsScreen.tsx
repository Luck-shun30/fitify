import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../theme/theme';
import { Card } from '../components/Card';
import { apiService } from '../services/api';

interface OutfitSuggestionsScreenProps {
  navigation: any;
  route: {
    params: {
      location: string;
      activity: string;
      formality: string;
      suggestions: any;
    };
  };
}

export const OutfitSuggestionsScreen: React.FC<OutfitSuggestionsScreenProps> = ({
  navigation,
  route,
}) => {
  const { location, activity, formality, suggestions } = route.params;
  const [loading, setLoading] = React.useState(false);

  const handleWearOutfit = async (outfit: any) => {
    try {
      setLoading(true);
      await apiService.logOutfit({
        outfit_id: outfit.name.toLowerCase().replace(/\s+/g, '_'),
        items: outfit.items,
        date_worn: new Date().toISOString(),
        weather: suggestions.weather,
        activity,
        formality,
      });
      navigation.navigate('Home');
    } catch (error) {
      console.error('Error logging outfit:', error);
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
          <Text style={styles.title}>Suggested Outfits</Text>
        </View>

        <Card style={styles.contextCard}>
          <View style={styles.contextRow}>
            <Ionicons name="location-outline" size={20} color={theme.colors.text} />
            <Text style={styles.contextText}>{location}</Text>
          </View>
          <View style={styles.contextRow}>
            <Ionicons name="calendar-outline" size={20} color={theme.colors.text} />
            <Text style={styles.contextText}>{activity}</Text>
          </View>
          <View style={styles.contextRow}>
            <Ionicons name="shirt-outline" size={20} color={theme.colors.text} />
            <Text style={styles.contextText}>{formality}</Text>
          </View>
        </Card>

        {suggestions.outfits.map((outfit: any, index: number) => (
          <Card key={index} style={styles.outfitCard}>
            <Text style={styles.outfitName}>{outfit.name}</Text>
            <View style={styles.itemsContainer}>
              {outfit.items.map((item: string) => (
                <View key={item} style={styles.itemContainer}>
                  <Image
                    source={{ uri: `https://fitify-07vt.onrender.com/wardrobe/${item}` }}
                    style={styles.itemImage}
                  />
                  <Text style={styles.itemName}>{item}</Text>
                </View>
              ))}
            </View>
            <Text style={styles.styleNotes}>{outfit.style_notes}</Text>
            <Text style={styles.weatherCompatibility}>
              {outfit.weather_compatibility}
            </Text>
            <TouchableOpacity
              style={styles.wearButton}
              onPress={() => handleWearOutfit(outfit)}
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
                    <Text style={styles.buttonText}>Wear This Outfit</Text>
                    <Ionicons name="checkmark" size={24} color={theme.colors.text} />
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </Card>
        ))}

        <Card style={styles.recommendationsCard}>
          <Text style={styles.recommendationsTitle}>Additional Tips</Text>
          {suggestions.recommendations.map((recommendation: string, index: number) => (
            <View key={index} style={styles.recommendationRow}>
              <Ionicons name="information-circle-outline" size={20} color={theme.colors.text} />
              <Text style={styles.recommendationText}>{recommendation}</Text>
            </View>
          ))}
        </Card>
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
  contextCard: {
    marginBottom: theme.spacing.lg,
  },
  contextRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  contextText: {
    ...theme.typography.body,
    color: theme.colors.text,
    marginLeft: theme.spacing.sm,
  },
  outfitCard: {
    marginBottom: theme.spacing.lg,
  },
  outfitName: {
    ...theme.typography.h3,
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  itemsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: theme.spacing.md,
  },
  itemContainer: {
    alignItems: 'center',
    marginRight: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  itemImage: {
    width: 80,
    height: 80,
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing.xs,
  },
  itemName: {
    ...theme.typography.caption,
    color: theme.colors.text,
  },
  styleNotes: {
    ...theme.typography.body,
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  weatherCompatibility: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  wearButton: {
    borderRadius: theme.borderRadius.lg,
    overflow: 'hidden',
    ...theme.shadows.medium,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.md,
  },
  buttonText: {
    ...theme.typography.h3,
    color: theme.colors.text,
    marginRight: theme.spacing.sm,
  },
  recommendationsCard: {
    marginBottom: theme.spacing.lg,
  },
  recommendationsTitle: {
    ...theme.typography.h3,
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  recommendationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  recommendationText: {
    ...theme.typography.body,
    color: theme.colors.text,
    marginLeft: theme.spacing.sm,
    flex: 1,
  },
}); 
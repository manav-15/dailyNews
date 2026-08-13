import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ??
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000');
const API_KEY = process.env.EXPO_PUBLIC_API_KEY ?? '';

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 30; // ~60s, well inside the backend's 5-minute cache TTL

const palettes = {
  dark: {
    bg: '#25221F',
    surface: '#302C28',
    surfaceSoft: '#3A3530',
    text: '#E9DEC8',
    textMuted: '#C2B6A7',
    textFaint: '#9C9185',
    line: '#70675B',
    signal: '#A8C8B1',
    accent: '#D79C45',
    accentText: '#25221F',
    danger: '#F0A49A',
  },
  light: {
    bg: '#F4EEE3',
    surface: '#FFF9F0',
    surfaceSoft: '#EAE1D2',
    text: '#302C28',
    textMuted: '#685E55',
    textFaint: '#81766B',
    line: '#CDC3B5',
    signal: '#59776A',
    accent: '#BD8536',
    accentText: '#FFF9F0',
    danger: '#B4473F',
  },
} as const;

type ThemeName = keyof typeof palettes;
type DigestItem = {
  id: string;
  source: string;
  title?: string;
  short?: string;
  long?: string;
  url?: string;
  author?: string;
  score?: number;
  published_at?: string;
};

type DigestTopic = {
  topic: string;
  summary?: string;
  items: DigestItem[];
};

type Digest = {
  date: string;
  generated_at?: string;
  topics: DigestTopic[];
};

function apiHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
  };
}

function storyTitle(item: DigestItem): string {
  return item.title?.trim() || item.short?.trim() || 'Untitled story';
}

function shouldShowShort(item: DigestItem): boolean {
  const short = item.short?.trim();
  return Boolean(short && short !== storyTitle(item));
}

function formatUpdatedAt(generatedAt?: string): string | null {
  if (!generatedAt) return null;
  const date = new Date(generatedAt);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatPublishedAt(publishedAt?: string): string | null {
  if (!publishedAt) return null;
  const date = new Date(publishedAt);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function formatDate(dateString?: string): string {
  if (!dateString) return 'Your daily briefing';
  const date = new Date(`${dateString}T12:00:00`);
  if (Number.isNaN(date.getTime())) return 'Your daily briefing';
  return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

function storyMeta(item: DigestItem): string {
  const parts = [item.source];
  if (item.author) parts.push(item.author);
  const publishedAt = formatPublishedAt(item.published_at);
  if (publishedAt) parts.push(publishedAt);
  return parts.join(' · ');
}

export default function App() {
  const [topics, setTopics] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<ThemeName>('dark');
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [showTopicManager, setShowTopicManager] = useState(false);
  const [pendingRemoval, setPendingRemoval] = useState<string | null>(null);
  const colors = palettes[theme];

  const loadTopics = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/topics`, { headers: apiHeaders() });
      const data = (await response.json()) as { raw_prompt: string }[];
      setTopics(data.map((topic) => topic.raw_prompt));
    } catch {
      /* The app remains usable while the backend is unavailable. */
    }
  }, []);

  const loadDigest = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/digest/today`, { headers: apiHeaders() });
      if (response.ok) setDigest(await response.json());
    } catch {
      /* A first-time user has no digest yet. */
    }
  }, []);

  useEffect(() => {
    loadTopics();
    loadDigest();
  }, [loadDigest, loadTopics]);

  useEffect(() => {
    if (selectedTopic && !digest?.topics.some((topic) => topic.topic === selectedTopic)) {
      setSelectedTopic(null);
    }
  }, [digest?.topics, selectedTopic]);

  const visibleTopics = useMemo(() => {
    if (!digest) return [];
    if (!selectedTopic) return digest.topics;
    return digest.topics.filter((topic) => topic.topic === selectedTopic);
  }, [digest, selectedTopic]);

  const syncTopics = async (next: string[]) => {
    const response = await fetch(`${API_BASE}/topics`, {
      method: 'PUT',
      headers: apiHeaders(),
      body: JSON.stringify({ topics: next.map((raw_prompt) => ({ raw_prompt })) }),
    });
    if (!response.ok) throw new Error(`topics ${response.status}`);
    const data = (await response.json()) as { raw_prompt: string }[];
    setTopics(data.map((topic) => topic.raw_prompt));
  };

  const addTopic = async () => {
    const prompt = input.trim();
    if (!prompt) return;
    setLoading(true);
    setError(null);
    try {
      await syncTopics(Array.from(new Set([...topics.filter((topic) => topic !== prompt), prompt])));
      setInput('');
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    } finally {
      setLoading(false);
    }
  };

  const removeTopic = async (prompt: string) => {
    setLoading(true);
    setError(null);
    try {
      await syncTopics(topics.filter((topic) => topic !== prompt));
      if (selectedTopic === prompt) setSelectedTopic(null);
      setPendingRemoval(null);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    } finally {
      setLoading(false);
    }
  };

  const pollForDigest = async (): Promise<void> => {
    for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
      const response = await fetch(`${API_BASE}/digest/today`, { headers: apiHeaders() });
      if (response.ok) {
        setDigest(await response.json());
        return;
      }
      if (response.status !== 404) throw new Error(`digest ${response.status}`);
      await new Promise<void>((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }
    throw new Error('Refresh timed out — try again');
  };

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/refresh`, { method: 'POST', headers: apiHeaders() });
      if (response.status === 200) {
        setDigest(await response.json()); // cached/fresh — immediate
      } else if (response.status === 202) {
        await pollForDigest(); // async run — poll until ready
      } else {
        throw new Error(`refresh ${response.status}`);
      }
      await loadTopics();
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    } finally {
      setLoading(false);
    }
  };

  const updatedAt = formatUpdatedAt(digest?.generated_at);
  const digestTopics = digest?.topics ?? [];

  return (
    <View style={[styles.screen, { backgroundColor: colors.bg }]}>
      <StatusBar style={theme === 'dark' ? 'light' : 'dark'} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <View>
            <Text style={[styles.masthead, { color: colors.signal }]}>DAILYNEWS</Text>
            <Text style={[styles.date, { color: colors.text }]}>{formatDate(digest?.date)}</Text>
            <Text style={[styles.updatedAt, { color: colors.textFaint }]}>
              {updatedAt ? `Updated ${updatedAt}` : 'Your daily briefing'}
            </Text>
          </View>
          <View style={[styles.themeSwitch, { borderColor: colors.line, backgroundColor: colors.surfaceSoft }]}>
            <Pressable
              accessibilityLabel="Use dark theme"
              accessibilityRole="button"
              onPress={() => setTheme('dark')}
              style={[styles.themeOption, theme === 'dark' && { backgroundColor: colors.accent }]}
            >
              <Text style={[styles.themeOptionText, { color: theme === 'dark' ? colors.accentText : colors.textMuted }]}>Dark</Text>
            </Pressable>
            <Pressable
              accessibilityLabel="Use light theme"
              accessibilityRole="button"
              onPress={() => setTheme('light')}
              style={[styles.themeOption, theme === 'light' && { backgroundColor: colors.accent }]}
            >
              <Text style={[styles.themeOptionText, { color: theme === 'light' ? colors.accentText : colors.textMuted }]}>Light</Text>
            </Pressable>
          </View>
        </View>

        <View style={[styles.divider, { backgroundColor: colors.accent }]} />

        <View style={styles.actions}>
          <Pressable
            accessibilityRole="button"
            onPress={() => setShowTopicManager((value) => !value)}
            style={[styles.followButton, { borderColor: colors.line, backgroundColor: colors.surface }]}
          >
            <Text style={[styles.followButtonText, { color: colors.text }]}>{showTopicManager ? 'Close topics' : '+ Follow a topic'}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            disabled={loading}
            onPress={refresh}
            style={({ pressed }) => [styles.refreshButton, { backgroundColor: colors.accent }, (pressed || loading) && styles.pressed]}
          >
            {loading ? <ActivityIndicator color={colors.accentText} /> : <Text style={[styles.refreshText, { color: colors.accentText }]}>Refresh</Text>}
          </Pressable>
        </View>

        {showTopicManager && (
          <View style={[styles.topicManager, { borderColor: colors.line, backgroundColor: colors.surface }]}>
            <View style={styles.composer}>
              <TextInput
                style={[styles.input, { color: colors.text, backgroundColor: colors.surfaceSoft, borderColor: colors.line }]}
                placeholder="Follow a topic (e.g. ‘oracle cloud’)"
                placeholderTextColor={colors.textFaint}
                value={input}
                onChangeText={setInput}
                onSubmitEditing={addTopic}
                returnKeyType="done"
              />
              <Pressable disabled={loading} onPress={addTopic} style={[styles.addButton, { backgroundColor: colors.signal }, loading && styles.pressed]}>
                <Text style={[styles.addButtonText, { color: theme === 'dark' ? '#25221F' : '#FFF9F0' }]}>Add</Text>
              </Pressable>
            </View>
            {topics.length > 0 && (
              <View style={styles.managedTopics}>
                {topics.map((topic) => (
                  <View key={topic} style={[styles.managedTopic, { borderColor: colors.line }]}>
                    <Text style={[styles.managedTopicText, { color: colors.text }]} numberOfLines={1}>{topic}</Text>
                    <Pressable
                      accessibilityRole="button"
                      accessibilityLabel={`Remove ${topic}`}
                      onPress={() => setPendingRemoval(topic)}
                      style={[styles.removeButton, { borderColor: colors.line }]}
                    >
                      <Text style={[styles.removeButtonText, { color: colors.textMuted }]}>Remove</Text>
                    </Pressable>
                  </View>
                ))}
              </View>
            )}
            {pendingRemoval && (
              <View style={[styles.removeConfirmation, { borderColor: colors.line, backgroundColor: colors.surfaceSoft }]}>
                <Text style={[styles.removeConfirmationTitle, { color: colors.text }]}>Remove {pendingRemoval}?</Text>
                <Text style={[styles.removeConfirmationCopy, { color: colors.textMuted }]}>You will stop receiving future briefings for this topic.</Text>
                <View style={styles.removeConfirmationActions}>
                  <Pressable disabled={loading} onPress={() => setPendingRemoval(null)} style={[styles.cancelRemovalButton, { borderColor: colors.line }]}>
                    <Text style={[styles.cancelRemovalText, { color: colors.text }]}>Keep topic</Text>
                  </Pressable>
                  <Pressable disabled={loading} onPress={() => removeTopic(pendingRemoval)} style={[styles.confirmRemovalButton, { backgroundColor: colors.danger }, loading && styles.pressed]}>
                    <Text style={[styles.confirmRemovalText, { color: colors.bg }]}>Remove topic</Text>
                  </Pressable>
                </View>
              </View>
            )}
          </View>
        )}

        {digestTopics.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.topicRail} style={styles.topicRailScroll}>
            <Pressable
              onPress={() => setSelectedTopic(null)}
              style={[styles.topicPill, { borderColor: colors.line }, !selectedTopic && { backgroundColor: colors.accent, borderColor: colors.accent }]}
            >
              <Text style={[styles.topicPillText, { color: !selectedTopic ? colors.accentText : colors.text }]} numberOfLines={1}>All topics</Text>
            </Pressable>
            {digestTopics.map((topic) => {
              const isActive = selectedTopic === topic.topic;
              return (
                <Pressable
                  key={topic.topic}
                  onPress={() => setSelectedTopic(topic.topic)}
                  style={[styles.topicPill, { borderColor: colors.line }, isActive && { backgroundColor: colors.accent, borderColor: colors.accent }]}
                >
                  <Text style={[styles.topicPillText, { color: isActive ? colors.accentText : colors.text }]} numberOfLines={1}>{topic.topic}</Text>
                </Pressable>
              );
            })}
          </ScrollView>
        )}

        {error && <Text style={[styles.error, { color: colors.danger }]}>{error}</Text>}

        {!digest && !loading && <Text style={[styles.empty, { color: colors.textMuted }]}>Follow a topic, then refresh your first briefing.</Text>}
        {digest && digestTopics.length === 0 && <Text style={[styles.empty, { color: colors.textMuted }]}>No topics yet — follow one above, then refresh.</Text>}

        <View style={styles.feed}>
          {visibleTopics.map((topic, index) => (
            <View key={topic.topic} style={styles.topicSection}>
              {index > 0 && <View style={[styles.sectionRule, { backgroundColor: colors.line }]} />}
              <View style={[styles.topicBand, { backgroundColor: colors.surfaceSoft, borderLeftColor: colors.accent }]}>
                <Text style={[styles.topicKicker, { color: colors.signal }]}>Topic briefing · {topic.items.length} {topic.items.length === 1 ? 'story' : 'stories'}</Text>
                <View style={styles.topicHeading}>
                  <Text style={[styles.topicTitle, { color: colors.text }]}>{topic.topic}</Text>
                </View>
              </View>
              {topic.summary ? <Text style={[styles.topicSummary, { color: colors.textMuted }]}>{topic.summary}</Text> : null}
              {topic.items.length === 0 ? (
                <Text style={[styles.noStories, { color: colors.textFaint }]}>No new matching stories today.</Text>
              ) : (
                <View>
                  {topic.items.map((item) => {
                    const canOpen = Boolean(item.url);
                    return (
                      <Pressable
                        key={item.id}
                        accessibilityRole={canOpen ? 'link' : 'text'}
                        accessibilityLabel={canOpen ? `Open ${storyTitle(item)} from ${item.source}` : `${storyTitle(item)} from ${item.source}`}
                        disabled={!canOpen}
                        onPress={() => item.url && Linking.openURL(item.url)}
                        style={({ pressed }) => [styles.story, { borderTopColor: colors.line }, canOpen && pressed && styles.pressed]}
                      >
                        <Text style={[styles.storyTitle, { color: colors.text }]}>{storyTitle(item)}{canOpen ? <Text style={[styles.externalMark, { color: colors.accent }]}> ↗</Text> : null}</Text>
                        {shouldShowShort(item) ? <Text style={[styles.storyShort, { color: colors.textMuted }]}>{item.short}</Text> : null}
                        <Text style={[styles.storyMeta, { color: colors.textFaint }]}>{storyMeta(item)}</Text>
                      </Pressable>
                    );
                  })}
                </View>
              )}
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  scrollContent: { paddingTop: 60, paddingBottom: 52 },
  header: { paddingHorizontal: 20, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  masthead: { fontSize: 12, fontWeight: '700', letterSpacing: 2.1 },
  date: { marginTop: 7, fontFamily: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }), fontSize: 27, lineHeight: 31 },
  updatedAt: { marginTop: 4, fontSize: 13, lineHeight: 18 },
  themeSwitch: { flexDirection: 'row', borderRadius: 999, borderWidth: 1, padding: 3, gap: 2 },
  themeOption: { borderRadius: 999, paddingVertical: 6, paddingHorizontal: 8 },
  themeOptionText: { fontSize: 11, fontWeight: '700' },
  divider: { height: 2, marginHorizontal: 20, marginTop: 20 },
  actions: { paddingHorizontal: 20, paddingTop: 16, flexDirection: 'row', gap: 8 },
  followButton: { flex: 1, minHeight: 44, borderWidth: 1, borderRadius: 999, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 14 },
  followButtonText: { fontSize: 14, fontWeight: '600' },
  refreshButton: { minHeight: 44, minWidth: 92, borderRadius: 999, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 16 },
  refreshText: { fontSize: 14, fontWeight: '700' },
  topicManager: { marginHorizontal: 20, marginTop: 12, padding: 12, borderWidth: 1, borderRadius: 14 },
  composer: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  input: { flex: 1, minHeight: 42, borderWidth: 1, borderRadius: 10, paddingHorizontal: 11, fontSize: 13 },
  addButton: { minHeight: 42, borderRadius: 999, justifyContent: 'center', paddingHorizontal: 14 },
  addButtonText: { fontSize: 13, fontWeight: '700' },
  managedTopics: { gap: 7, marginTop: 10 },
  managedTopic: { maxWidth: '100%', minHeight: 40, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 10, paddingVertical: 5, paddingLeft: 10, paddingRight: 6, gap: 8 },
  managedTopicText: { flex: 1, fontSize: 12 },
  removeButton: { minHeight: 30, borderWidth: 1, borderRadius: 999, justifyContent: 'center', paddingHorizontal: 9 },
  removeButtonText: { fontSize: 11, fontWeight: '700' },
  removeConfirmation: { marginTop: 10, borderWidth: 1, borderRadius: 12, padding: 11 },
  removeConfirmationTitle: { fontFamily: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }), fontSize: 16, lineHeight: 20 },
  removeConfirmationCopy: { marginTop: 3, fontSize: 12, lineHeight: 17 },
  removeConfirmationActions: { flexDirection: 'row', gap: 8, marginTop: 10 },
  cancelRemovalButton: { flex: 1, minHeight: 38, borderWidth: 1, borderRadius: 999, justifyContent: 'center', alignItems: 'center' },
  cancelRemovalText: { fontSize: 12, fontWeight: '700' },
  confirmRemovalButton: { flex: 1, minHeight: 38, borderRadius: 999, justifyContent: 'center', alignItems: 'center' },
  confirmRemovalText: { fontSize: 12, fontWeight: '700' },
  topicRailScroll: { marginTop: 17 },
  topicRail: { paddingHorizontal: 20, gap: 7 },
  topicPill: { borderWidth: 1, borderRadius: 999, paddingVertical: 8, paddingHorizontal: 12 },
  topicPillText: { fontSize: 13, fontWeight: '600' },
  error: { paddingHorizontal: 20, paddingTop: 12, fontSize: 13 },
  empty: { paddingHorizontal: 32, marginTop: 62, textAlign: 'center', fontFamily: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }), fontSize: 18, lineHeight: 25 },
  feed: { paddingHorizontal: 20, paddingTop: 22 },
  topicSection: { paddingBottom: 28 },
  sectionRule: { height: 1, marginBottom: 24 },
  topicBand: { marginBottom: 10, marginHorizontal: -20, paddingTop: 12, paddingBottom: 12, paddingHorizontal: 20, borderLeftWidth: 3 },
  topicKicker: { marginBottom: 5, fontSize: 10, fontWeight: '700', letterSpacing: 1.1, textTransform: 'uppercase' },
  topicHeading: { flexDirection: 'row', alignItems: 'baseline' },
  topicTitle: { flex: 1, fontFamily: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }), fontSize: 25, lineHeight: 30 },
  topicSummary: { marginTop: 7, marginBottom: 8, fontSize: 14, lineHeight: 21 },
  noStories: { paddingTop: 14, paddingBottom: 4, fontSize: 14 },
  story: { minHeight: 56, paddingVertical: 13, borderTopWidth: 1 },
  storyTitle: { fontSize: 16, lineHeight: 22, fontWeight: '700' },
  externalMark: { fontSize: 15 },
  storyShort: { marginTop: 5, fontSize: 13, lineHeight: 19 },
  storyMeta: { marginTop: 5, fontSize: 12, lineHeight: 16 },
  pressed: { opacity: 0.62 },
});

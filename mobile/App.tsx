import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
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

function apiHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
  };
}

const colors = {
  bg: '#f6f7f8',
  surface: '#ffffff',
  surfaceAlt: '#eef0f3',
  border: '#e3e6ea',
  text: '#17191c',
  textMuted: '#4b535d',
  textFaint: '#7d8793',
  accent: '#2f6fe4',
  accentText: '#2f6fe4',
  danger: '#d64545',
};

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

function metaLine(item: DigestItem): string {
  const parts = [item.source];
  if (item.author) parts.push(item.author);
  if (item.score != null) parts.push(`${item.score} pts`);
  return parts.join(' · ');
}

export default function App() {
  const [topics, setTopics] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTopics = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/topics`, { headers: apiHeaders() });
      const data = (await r.json()) as { raw_prompt: string }[];
      setTopics(data.map((t) => t.raw_prompt));
    } catch {
      /* backend not reachable yet */
    }
  }, []);

  const loadDigest = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/digest/today`, { headers: apiHeaders() });
      if (r.ok) setDigest(await r.json());
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadTopics();
    loadDigest();
  }, [loadTopics, loadDigest]);

  const syncTopics = async (next: string[]) => {
    const r = await fetch(`${API_BASE}/topics`, {
      method: 'PUT',
      headers: apiHeaders(),
      body: JSON.stringify({ topics: next.map((t) => ({ raw_prompt: t })) }),
    });
    if (!r.ok) throw new Error(`topics ${r.status}`);
    const data = (await r.json()) as { raw_prompt: string }[];
    setTopics(data.map((t) => t.raw_prompt));
  };

  const addTopic = async () => {
    const prompt = input.trim();
    if (!prompt) return;
    setLoading(true);
    setError(null);
    try {
      await syncTopics(Array.from(new Set([...topics.filter((t) => t !== prompt), prompt])));
      setInput('');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const removeTopic = async (prompt: string) => {
    setLoading(true);
    setError(null);
    try {
      await syncTopics(topics.filter((t) => t !== prompt));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API_BASE}/refresh`, { method: 'POST', headers: apiHeaders() });
      if (!r.ok) throw new Error(`refresh ${r.status}`);
      setDigest(await r.json());
      loadTopics();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const updatedAt = digest?.generated_at
    ? new Date(digest.generated_at).toLocaleString()
    : null;

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />

      <View style={styles.header}>
        <Text style={styles.appTitle}>Daily Digest</Text>
        <Text style={styles.appSubtitle}>
          {updatedAt ? `Updated ${updatedAt}` : 'Your daily briefing'}
        </Text>
      </View>

      <View style={styles.composer}>
        <TextInput
          style={styles.input}
          placeholder="Add a topic (e.g. 'oracle cloud')"
          placeholderTextColor={colors.textFaint}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={addTopic}
          returnKeyType="done"
        />
        <Pressable style={styles.addButton} onPress={addTopic} disabled={loading}>
          <Text style={styles.addButtonText}>Add</Text>
        </Pressable>
      </View>

      {topics.length > 0 && (
        <View style={styles.chipRow}>
          {topics.map((t) => (
            <Pressable key={t} style={styles.chip} onPress={() => removeTopic(t)}>
              <Text style={styles.chipText}>{t}</Text>
              <Text style={styles.chipX}> ×</Text>
            </Pressable>
          ))}
        </View>
      )}

      <Pressable style={styles.refresh} onPress={refresh} disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.refreshText}>Refresh digest</Text>
        )}
      </Pressable>

      {error && <Text style={styles.error}>{error}</Text>}

      <ScrollView contentContainerStyle={styles.body}>
        {!digest && !loading && (
          <Text style={styles.empty}>Add topics above, then tap "Refresh digest".</Text>
        )}
        {digest && digest.topics.length === 0 && (
          <Text style={styles.empty}>No topics yet — add one above, then refresh.</Text>
        )}

        {digest?.topics.map((topic) => (
          <View key={topic.topic} style={styles.card}>
            <Text style={styles.topicTitle}>{topic.topic}</Text>
            {topic.summary ? <Text style={styles.summary}>{topic.summary}</Text> : null}

            <View style={styles.items}>
              {topic.items.map((item) => (
                <Pressable
                  key={item.id}
                  style={({ pressed }) => [styles.item, pressed && styles.itemPressed]}
                  onPress={() => item.url && Linking.openURL(item.url)}
                >
                  <Text style={styles.itemTitle}>{item.title}</Text>
                  <Text style={styles.meta}>{metaLine(item)}</Text>
                  {item.short && item.short !== item.title ? (
                    <Text style={styles.itemShort}>{item.short}</Text>
                  ) : null}
                </Pressable>
              ))}
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },

  header: { paddingTop: 60, paddingHorizontal: 20, paddingBottom: 16 },
  appTitle: { color: colors.text, fontSize: 26, fontWeight: '700', letterSpacing: -0.3 },
  appSubtitle: { color: colors.textFaint, fontSize: 13, marginTop: 3 },

  composer: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 20 },
  input: {
    flex: 1,
    backgroundColor: colors.surfaceAlt,
    color: colors.text,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 11,
    fontSize: 15,
  },
  addButton: {
    backgroundColor: colors.accent,
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 11,
  },
  addButtonText: { color: '#fff', fontWeight: '600', fontSize: 15 },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, paddingHorizontal: 20, paddingTop: 12 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceAlt,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chipText: { color: colors.accentText, fontSize: 13 },
  chipX: { color: colors.textFaint, fontSize: 13 },

  refresh: {
    backgroundColor: colors.accent,
    borderRadius: 10,
    marginHorizontal: 20,
    marginTop: 16,
    paddingVertical: 13,
    alignItems: 'center',
  },
  refreshText: { color: '#fff', fontWeight: '600', fontSize: 15 },

  error: { color: colors.danger, paddingHorizontal: 20, paddingTop: 10, fontSize: 13 },

  body: { padding: 20, gap: 20, paddingBottom: 40 },
  empty: { color: colors.textFaint, textAlign: 'center', marginTop: 40, fontSize: 14 },

  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 16,
    gap: 10,
  },
  topicTitle: { color: colors.text, fontSize: 17, fontWeight: '700' },
  summary: { color: colors.textMuted, fontSize: 14, lineHeight: 21 },

  items: { gap: 0 },
  item: {
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  itemPressed: { opacity: 0.6 },
  itemTitle: { color: colors.text, fontSize: 15, fontWeight: '600', lineHeight: 21 },
  meta: { color: colors.textFaint, fontSize: 12, marginTop: 4 },
  itemShort: { color: colors.textMuted, fontSize: 13, lineHeight: 19, marginTop: 5 },
});

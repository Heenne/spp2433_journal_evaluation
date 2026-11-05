using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace SPP2433
{
    internal static class Program
    {
        [STAThread]
        private static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new LauncherForm(args));
        }
    }

    internal sealed class LauncherForm : Form
    {
        private readonly string[] arguments;
        private readonly ProgressBar progressBar;
        private readonly Label statusLabel;
        private readonly Label percentLabel;
        private readonly Button exitButton;
        private readonly string cacheParent;
        private readonly string cacheDirectory;
        private readonly string stagingDirectory;
        private readonly string cachedExecutable;

        internal LauncherForm(string[] args)
        {
            arguments = args;
            cacheParent = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "SPP2433", "p");
            cacheDirectory = Path.Combine(cacheParent, BuildInfo.CacheDirectoryName);
            stagingDirectory = cacheDirectory + ".partial";
            cachedExecutable = Path.Combine(
                cacheDirectory,
                BuildInfo.ApplicationExecutable);

            Text = "SPP 2433 - Point Cloud Evaluation";
            BackColor = Color.FromArgb(247, 248, 250);
            FormBorderStyle = FormBorderStyle.Sizable;
            StartPosition = FormStartPosition.Manual;
            ShowInTaskbar = true;
            MaximizeBox = false;
            TopMost = false;
            Bounds = InitialBounds();

            try
            {
                using (Stream iconStream = Assembly.GetExecutingAssembly()
                    .GetManifestResourceStream("SPP2433.AppIcon.ico"))
                {
                    if (iconStream != null) Icon = new Icon(iconStream);
                }
            }
            catch { }

            var logo = new PictureBox();
            logo.Size = new Size(128, 128);
            logo.Location = new Point((ClientSize.Width - 128) / 2, ClientSize.Height / 2 - 190);
            logo.SizeMode = PictureBoxSizeMode.Zoom;
            logo.BackColor = Color.Transparent;
            try
            {
                using (Stream logoStream = Assembly.GetExecutingAssembly()
                    .GetManifestResourceStream("SPP2433.AppLogo.png"))
                using (Image source = Image.FromStream(logoStream))
                {
                    logo.Image = new Bitmap(source);
                }
            }
            catch
            {
                logo.Image = Icon == null ? null : Icon.ToBitmap();
            }
            Controls.Add(logo);

            var brand = new Label();
            brand.Text = "SPP 2433";
            brand.Font = new Font("Segoe UI", 24, FontStyle.Bold);
            brand.ForeColor = Color.FromArgb(32, 41, 56);
            brand.TextAlign = ContentAlignment.MiddleCenter;
            brand.Location = new Point(0, ClientSize.Height / 2 - 48);
            brand.Size = new Size(ClientSize.Width, 46);
            Controls.Add(brand);

            var product = new Label();
            product.Text = "Point Cloud Evaluation";
            product.Font = new Font("Segoe UI", 14, FontStyle.Regular);
            product.ForeColor = Color.FromArgb(82, 97, 116);
            product.TextAlign = ContentAlignment.MiddleCenter;
            product.Location = new Point(0, ClientSize.Height / 2 + 2);
            product.Size = new Size(ClientSize.Width, 32);
            Controls.Add(product);

            statusLabel = new Label();
            statusLabel.Text = "Preparing application…";
            statusLabel.Font = new Font("Segoe UI", 10, FontStyle.Regular);
            statusLabel.ForeColor = Color.FromArgb(102, 112, 133);
            statusLabel.TextAlign = ContentAlignment.MiddleCenter;
            statusLabel.Location = new Point(0, ClientSize.Height / 2 + 80);
            statusLabel.Size = new Size(ClientSize.Width, 30);
            Controls.Add(statusLabel);

            progressBar = new ProgressBar();
            progressBar.Minimum = 0;
            progressBar.Maximum = 100;
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Location = new Point((ClientSize.Width - 520) / 2, ClientSize.Height / 2 + 116);
            progressBar.Size = new Size(520, 18);
            Controls.Add(progressBar);

            percentLabel = new Label();
            percentLabel.Text = "0%";
            percentLabel.Font = new Font("Segoe UI", 9, FontStyle.Regular);
            percentLabel.ForeColor = Color.FromArgb(82, 97, 116);
            percentLabel.TextAlign = ContentAlignment.MiddleCenter;
            percentLabel.Location = new Point(0, ClientSize.Height / 2 + 142);
            percentLabel.Size = new Size(ClientSize.Width, 24);
            Controls.Add(percentLabel);

            exitButton = new Button();
            exitButton.Text = "Beenden";
            exitButton.Size = new Size(110, 32);
            exitButton.Location = new Point((ClientSize.Width - exitButton.Width) / 2,
                ClientSize.Height / 2 + 180);
            exitButton.Anchor = AnchorStyles.Top;
            exitButton.Visible = false;
            exitButton.Click += (sender, eventArgs) => Close();
            Controls.Add(exitButton);

            Shown += OnShown;
        }

        private static Rectangle InitialBounds()
        {
            Rectangle available = Screen.FromPoint(Cursor.Position).WorkingArea;
            int minimumWidth = Math.Min(1050, Math.Max(1, available.Width - 32));
            int minimumHeight = Math.Min(700, Math.Max(1, available.Height - 32));
            int width = Math.Max(minimumWidth, Math.Min(1500, (int)Math.Round(available.Width * 0.9)));
            int height = Math.Max(minimumHeight, Math.Min(900, (int)Math.Round(available.Height * 0.9)));
            return new Rectangle(
                available.X + (available.Width - width) / 2,
                available.Y + (available.Height - height) / 2,
                width,
                height);
        }

        private async void OnShown(object sender, EventArgs eventArgs)
        {
            try
            {
                using (var mutex = new Mutex(false, "Local\\SPP2433PointCloudCache-" + BuildInfo.CacheKey))
                {
                    SetProgress(1, "Checking the local app cache…");
                    mutex.WaitOne();
                    try
                    {
                        if (!CacheIsReady())
                        {
                            SetProgress(0, "First start: preparing the app on this computer…");
                            var progress = new Progress<int>(value => SetProgress(value,
                                "First start: copying app files to your user profile…"));
                            await Task.Run(() => ExtractPayload(progress));
                        }
                        else
                        {
                            SetProgress(55, "App cache ready. Starting…");
                        }
                    }
                    finally
                    {
                        mutex.ReleaseMutex();
                    }
                }

                SetProgress(55, "Starting Point Cloud Evaluation…");
                var startInfo = new ProcessStartInfo();
                startInfo.FileName = cachedExecutable;
                startInfo.WorkingDirectory = Path.GetDirectoryName(cachedExecutable);
                startInfo.UseShellExecute = false;
                startInfo.EnvironmentVariables["SPP2433_STARTUP_PROGRESS"] = "55";
                startInfo.Arguments = String.Join(" ", arguments.Select(QuoteArgument).ToArray());
                Process.Start(startInfo);
                Close();
            }
            catch (Exception exception)
            {
                statusLabel.Text = "Start fehlgeschlagen: " + exception.Message;
                percentLabel.Text = "Fehler";
                exitButton.Visible = true;
                Activate();
            }
        }

        private bool CacheIsReady()
        {
            string marker = Path.Combine(cacheDirectory, ".payload-ready");
            return File.Exists(marker)
                && File.ReadAllText(marker).Trim() == BuildInfo.CacheKey
                && File.Exists(cachedExecutable)
                && Directory.Exists(Path.Combine(cacheDirectory, "_internal"));
        }

        private void ExtractPayload(IProgress<int> progress)
        {
            Directory.CreateDirectory(cacheParent);
            if (Directory.Exists(stagingDirectory)) Directory.Delete(stagingDirectory, true);
            if (Directory.Exists(cacheDirectory)) Directory.Delete(cacheDirectory, true);
            Directory.CreateDirectory(stagingDirectory);

            try
            {
                Assembly assembly = Assembly.GetExecutingAssembly();
                using (Stream payload = assembly.GetManifestResourceStream("SPP2433.Payload.zip"))
                {
                    if (payload == null) throw new InvalidOperationException("The embedded app archive is missing.");
                    using (var archive = new ZipArchive(payload, ZipArchiveMode.Read))
                    {
                        var entries = archive.Entries
                            .Where(entry => !String.IsNullOrEmpty(entry.Name))
                            .ToArray();
                        long totalBytes = entries.Sum(entry => entry.Length);
                        long copiedBytes = 0;
                        int lastProgress = -1;
                        byte[] buffer = new byte[1024 * 1024];
                        string rootPrefix = BuildInfo.PayloadRoot.TrimEnd('/', '\\') + "/";
                        string stagingRoot = Path.GetFullPath(stagingDirectory) + Path.DirectorySeparatorChar;

                        foreach (ZipArchiveEntry entry in entries)
                        {
                            string entryName = entry.FullName.Replace('\\', '/');
                            if (!entryName.StartsWith(rootPrefix, StringComparison.OrdinalIgnoreCase))
                                throw new InvalidDataException("The embedded archive has an unexpected folder layout.");

                            string relativePath = entryName.Substring(rootPrefix.Length)
                                .Replace('/', Path.DirectorySeparatorChar);
                            string destination = Path.GetFullPath(Path.Combine(stagingRoot, relativePath));
                            if (!destination.StartsWith(stagingRoot, StringComparison.OrdinalIgnoreCase))
                                throw new InvalidDataException("The embedded archive contains an invalid path.");

                            Directory.CreateDirectory(Path.GetDirectoryName(destination));
                            using (Stream input = entry.Open())
                            using (var output = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None))
                            {
                                int read;
                                while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
                                {
                                    output.Write(buffer, 0, read);
                                    copiedBytes += read;
                                    if (totalBytes > 0)
                                    {
                                        int value = (int)(copiedBytes * 55L / totalBytes);
                                        if (value != lastProgress)
                                        {
                                            lastProgress = value;
                                            progress.Report(value);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                File.WriteAllText(Path.Combine(stagingDirectory, ".payload-ready"), BuildInfo.CacheKey);
                Directory.Move(stagingDirectory, cacheDirectory);
                progress.Report(55);
            }
            catch
            {
                if (Directory.Exists(stagingDirectory)) Directory.Delete(stagingDirectory, true);
                throw;
            }
        }

        private void SetProgress(int value, string message)
        {
            progressBar.Value = Math.Max(progressBar.Minimum, Math.Min(progressBar.Maximum, value));
            percentLabel.Text = progressBar.Value + "%";
            statusLabel.Text = message;
            Application.DoEvents();
        }

        private static string QuoteArgument(string argument)
        {
            if (argument.Length > 0 && argument.All(character => !Char.IsWhiteSpace(character) && character != '"'))
                return argument;

            var result = new System.Text.StringBuilder("\"");
            int backslashes = 0;
            foreach (char character in argument)
            {
                if (character == '\\')
                {
                    backslashes++;
                }
                else if (character == '"')
                {
                    result.Append('\\', backslashes * 2 + 1);
                    result.Append('"');
                    backslashes = 0;
                }
                else
                {
                    result.Append('\\', backslashes);
                    result.Append(character);
                    backslashes = 0;
                }
            }
            result.Append('\\', backslashes * 2);
            result.Append('"');
            return result.ToString();
        }
    }
}

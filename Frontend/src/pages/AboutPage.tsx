// src/pages/AboutPage.tsx
import { motion } from "framer-motion";
import { Github, Mail, User } from "lucide-react";

const GITHUB_URL = "https://github.com/statjhw/MangMangDae-AI"; // TODO: 너희 깃헙 주소
const NAME = "MMD"; // TODO: 이름
const EMAIL = "we1905@naver.com"; // TODO: 이메일

const AboutPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-secondary-50 to-primary-50 pt-16">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white py-20">
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.h1
            className="text-4xl md:text-5xl font-bold"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            소개
          </motion.h1>
          <p className="mt-4 text-primary-100">
            망망대 AI 팀 및 프로젝트 정보
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-sm border border-secondary-200 p-8 space-y-8">
            {/* Name */}
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-primary-50">
                <User className="h-6 w-6 text-primary-700" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-secondary-900">이름</h3>
                <p className="text-secondary-600">{NAME}</p>
              </div>
            </div>

            {/* GitHub */}
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-primary-50">
                <Github className="h-6 w-6 text-primary-700" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-secondary-900">GitHub</h3>
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-700 hover:underline break-all"
                >
                  {GITHUB_URL}
                </a>
              </div>
            </div>

            {/* Email */}
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-primary-50">
                <Mail className="h-6 w-6 text-primary-700" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-secondary-900">이메일</h3>
                <a
                  href={`mailto:${EMAIL}`}
                  className="text-primary-700 hover:underline break-all"
                >
                  {EMAIL}
                </a>
              </div>
            </div>

            <p className="text-sm text-secondary-500">
              * 위 정보는 언제든 변경될 수 있으며, 최신 정보는 GitHub 리포지토리를 참고해주세요.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;